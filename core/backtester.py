"""백테스트 엔진

과거 캔들 데이터를 순차적으로 시뮬레이션하며 Calculator + Position 로직을 동일하게 적용합니다.
산출 지표:
    - total_trades : 총 거래 횟수
    - win_rate     : 승률
    - total_pnl    : 총 손익 (절대값, 기준 통화)
    - max_drawdown : 최대 낙폭 (%)
    - trades       : 개별 트레이드 상세 (진입/청산/보유시간)

단순화 가정:
    - 심볼별 동시에 하나의 포지션만 (스케일 인/아웃 없음)
    - 거래 단위 1 (PnL = 출구가격 - 진입가격)
    - buy 액션 시 해당 캔들 종가로 진입, sell 액션 시 해당 캔들 종가로 청산

향후 확장: 수수료, 슬리피지, 다중 타임프레임, 포지션 사이징 등.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Any
from .calculator import Calculator
from .position import decide_action
from .loader import HistoricalLoader

class Backtester:
    def __init__(self, settings_path: str = "config/settings.json", methods_path: str = "methods", historical_dir: str = "data/historical"):
        self.calc = Calculator(settings_path, methods_path)
        self.loader = HistoricalLoader(historical_dir)

    def run(self, symbols: List[str], limit: Optional[int] = None) -> Dict[str, Any]:
        trades: List[Dict[str, Any]] = []
        total_pnl = 0.0
        equity_curve: List[float] = []

        for symbol in symbols:
            candles = self.loader.load(symbol, limit=limit)
            if not candles:
                continue
            position_open = False
            entry_price: Optional[float] = None
            entry_time: Optional[int] = None

            for idx in range(len(candles)):
                window = candles[: idx + 1]
                latest = window[-1]
                score = self.calc.compute_symbol(symbol, window)
                current_price = latest["close"]
                action = decide_action(score, position_open, entry_price, current_price)

                if not position_open and action == "buy":
                    position_open = True
                    entry_price = current_price
                    entry_time = latest["timestamp"]
                elif position_open and action == "sell":
                    exit_price = current_price
                    pnl = exit_price - (entry_price or exit_price)
                    hold_minutes = int((latest["timestamp"] - (entry_time or latest["timestamp"])) / 60)
                    trades.append({
                        "symbol": symbol,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": round(pnl, 4),
                        "hold_time_minutes": hold_minutes,
                    })
                    total_pnl += pnl
                    position_open = False
                    entry_price = None
                    entry_time = None
                # 에퀴티 곡선 업데이트 (미실현 손익 포함 시 표시)
                if position_open and entry_price is not None:
                    unrealized = current_price - entry_price
                    equity_curve.append(total_pnl + unrealized)
                else:
                    equity_curve.append(total_pnl)

            # 마지막 캔들에서 미청산 포지션 강제 청산 (옵션)
            if position_open and entry_price is not None:
                last_price = candles[-1]["close"]
                pnl = last_price - entry_price
                hold_minutes = int((candles[-1]["timestamp"] - (entry_time or candles[-1]["timestamp"])) / 60)
                trades.append({
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "exit_price": last_price,
                    "pnl": round(pnl, 4),
                    "hold_time_minutes": hold_minutes,
                })
                total_pnl += pnl
                equity_curve.append(total_pnl)

        wins = sum(1 for t in trades if t["pnl"] > 0)
        total_trades = len(trades)
        win_rate = wins / total_trades if total_trades else 0.0
        max_drawdown = self._compute_max_drawdown(equity_curve)

        result = {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 4),
            "max_drawdown": round(max_drawdown, 4),
            "trades": trades,
        }
        return result

    @staticmethod
    def _compute_max_drawdown(equity: List[float]) -> float:
        if not equity:
            return 0.0
        peak = equity[0]
        max_dd = 0.0
        for value in equity:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak if peak != 0 else 0.0
            if drawdown < max_dd:
                max_dd = drawdown
        return max_dd * 100  # 퍼센트 반환

__all__ = ["Backtester"]
