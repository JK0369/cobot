"""포지션 & 액션 결정 로직

최종 매매 액션(buy/sell/hold)을 아래 요소로 판단:
    - 종합 점수 (-1..1)
    - 현재 포지션 보유 여부
    - 진입 가격과 현재 가격 차이(손익)

단순 규칙 (향후 고도화 가능):
    1. 포지션 없음 & score >= BUY_THRESHOLD -> buy
    2. 포지션 있음 & score <= SELL_THRESHOLD -> sell
    3. 포지션 있음 & 손실률 STOP_LOSS_PCT 이하 -> sell
    4. 그 외 hold

임계값 (가독성 위해 설정, 추후 조정 가능):
    BUY_THRESHOLD = 0.4
    SELL_THRESHOLD = -0.4
    STOP_LOSS_PCT = -0.05  ( -5% )
"""
from __future__ import annotations

from typing import Optional, Dict

BUY_THRESHOLD = 0.4
SELL_THRESHOLD = -0.4
STOP_LOSS_PCT = -0.05  # -5%

def decide_action(score: float, has_position: bool, entry_price: Optional[float], current_price: float) -> str:
    # score 범위 보정
    if score > 1:
        score = 1.0
    if score < -1:
        score = -1.0

    if not has_position:
        if score >= BUY_THRESHOLD:
            return "buy"
        else:
            return "hold"

    # 포지션 보유 상태
    if entry_price is None:
        # Defensive fallback
        return "hold"

    # 미실현 손익 비율 계산
    pnl_pct = (current_price - entry_price) / entry_price

    # 손절 조건
    if pnl_pct <= STOP_LOSS_PCT:
        return "sell"

    # 점수 기반 청산 조건
    if score <= SELL_THRESHOLD:
        return "sell"

    return "hold"

def build_output(symbol: str, score: float, has_position: bool, entry_price: Optional[float], current_price: float) -> Dict:
    action = decide_action(score, has_position, entry_price, current_price)
    return {
        symbol: {
            "score": round(score, 4),
            "has_position": bool(has_position),
            "entry_price": entry_price if has_position else None,
            "current_price": current_price,
            "action": action,
        }
    }

__all__ = ["decide_action", "build_output"]
