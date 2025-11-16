"""실시간 실행 진입점 (Stub)

실 서비스에서는:
    - 심볼/타임프레임별 Binance WebSocket 연결 유지
    - 새로운 데이터 도착 시에만 캔들 캐시 갱신 (성능 최적화)
    - 각 업데이트마다 Calculator + Position 로직 호출 → JSON 출력

현재는 데모를 위해 historical 데이터를 live 데이터 대용으로 사용합니다.
"""
from __future__ import annotations

import json
from typing import Dict, List
from core.calculator import Calculator
from core.loader import HistoricalLoader, LiveLoader
from core.position import build_output

SYMBOLS = ["BTC", "ETH"]

# 심볼별 예시 포지션 상태 (실제로는 외부 저장소에서 로딩 가능)
positions = {
    "BTC": {"has_position": False, "entry_price": None},
    "ETH": {"has_position": True, "entry_price": 3100.0},
}

def get_candles(symbol: str, historical: HistoricalLoader, live: LiveLoader, window: int = 100):
    live_candles = live.get_latest(symbol, limit=window)
    if len(live_candles) < 10:  # 실시간 데이터 부족 시 historical 대체
        return historical.load(symbol, limit=window)
    return live_candles

def run_once() -> Dict:
    calc = Calculator("config/settings.json", "methods")
    historical = HistoricalLoader()
    live = LiveLoader()
    result: Dict = {}
    for symbol in SYMBOLS:
        candles = get_candles(symbol, historical, live, window=120)
        if not candles:
            continue
        score = calc.compute_symbol(symbol, candles)
        current_price = candles[-1]["close"]
        p_state = positions.get(symbol, {"has_position": False, "entry_price": None})
        out = build_output(symbol, score, p_state["has_position"], p_state["entry_price"], current_price)
        result.update(out)
    return result

if __name__ == "__main__":  # pragma: no cover
    data = run_once()
    print(json.dumps(data, ensure_ascii=False, indent=2))
