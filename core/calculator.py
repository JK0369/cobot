"""점수 계산 엔진 (Calculator)

`methods/` 디렉터리 안의 분석 모듈을 동적으로 로딩하고 `settings.json`에 정의된
가중치로 개별 점수를 합산하여 최종 종합 점수(-1..1)를 계산합니다.

각 방법 모듈은 다음을 반드시 포함:
        METHOD_NAME: str
        compute(symbol: str, candles: list[dict]) -> float  # -1..1 반환

설정 파일 형식 (리스트):
[
    {"method": "volume_spike", "weight": 0.5},
    {"method": "rsi_oversold", "weight": 0.7}
]

사용 예:
        calc = Calculator(settings_path="config/settings.json", methods_path="methods")
        score = calc.compute_symbol("BTC", candles)

Candles: 메서드가 필요로 하는 최소 키('close','volume' 등)를 가진 dict 리스트.
가장 최신 캔들은 인덱스 -1.
"""
from __future__ import annotations

import json
import importlib.util
import os
from typing import Dict, List, Callable

class Calculator:
    def __init__(self, settings_path: str, methods_path: str):
        self.settings_path = settings_path
        self.methods_path = methods_path
        self.method_weights: Dict[str, float] = {}
        self.method_funcs: Dict[str, Callable] = {}
        self._load_settings()
        self._discover_methods()

    def _load_settings(self) -> None:
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")
        with open(self.settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.method_weights = {item["method"]: float(item.get("weight", 0)) for item in data}

    def _discover_methods(self) -> None:
        # methods_path 내 모든 .py 파일을 로드하고 settings에 등록된 METHOD_NAME 만 사용
        if not os.path.isdir(self.methods_path):
            raise FileNotFoundError(f"Methods directory not found: {self.methods_path}")
        for fname in os.listdir(self.methods_path):
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            path = os.path.join(self.methods_path, fname)
            spec = importlib.util.spec_from_file_location(fname[:-3], path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            method_name = getattr(module, "METHOD_NAME", None)
            compute_fn = getattr(module, "compute", None)
            if not method_name or not callable(compute_fn):
                continue
            if method_name in self.method_weights:
                self.method_funcs[method_name] = compute_fn

    def refresh(self) -> None:
        """settings.json 변경 시 가중치 및 메서드 재로딩"""
        self.method_weights.clear()
        self.method_funcs.clear()
        self._load_settings()
        self._discover_methods()

    def compute_symbol(self, symbol: str, candles: List[Dict]) -> float:
        if not self.method_funcs:
            return 0.0
        total_weight = sum(w for w in self.method_weights.values() if w > 0)
        if total_weight <= 0:
            return 0.0
        weighted_sum = 0.0
        for name, fn in self.method_funcs.items():
            weight = self.method_weights.get(name, 0)
            if weight <= 0:
                continue
            try:
                score = float(fn(symbol, candles))
            except Exception:
                score = 0.0  # 메서드 실행 오류 시 해당 항목은 0 처리
            weighted_sum += score * weight
        combined = weighted_sum / total_weight
        if combined > 1:
            combined = 1.0
        if combined < -1:
            combined = -1.0
        return round(combined, 4)

    def compute_all(self, symbol_candles: Dict[str, List[Dict]]) -> Dict[str, float]:
        return {sym: self.compute_symbol(sym, cnds) for sym, cnds in symbol_candles.items()}

__all__ = ["Calculator"]
