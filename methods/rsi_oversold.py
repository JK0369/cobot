"""RSI 과매수/과매도 기법

종가 배열로 RSI를 계산한 후 -1..1 범위 점수로 매핑합니다:
    - RSI <= 30 : 향후 반등 가능성으로 + 방향(매수 기회) 점수
    - RSI >= 70 : 하락/조정 가능성으로 - 방향(매도 기회) 점수
    - 중간 구간은 선형적으로 0 주변으로 스케일링

함수 규약:
        compute(symbol: str, candles: list[dict]) -> float
        각 캔들은 'close' 키를 포함해야 하며 최신 캔들은 candles[-1] 입니다.
"""
from __future__ import annotations

from typing import List, Dict

def _compute_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0  # 데이터 부족 시 중립 RSI
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = closes[-i] - closes[-i - 1]
        if change >= 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-change)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss if avg_loss > 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute(symbol: str, candles: List[Dict]) -> float:
    closes = [c.get("close", 0) for c in candles]
    rsi = _compute_rsi(closes)
    # RSI를 -1..1로 매핑: 50 -> 0 (중립)
    # 30 이하 -> +1 쪽, 70 이상 -> -1 쪽으로 선형 이동
    if rsi <= 30:
        score = (30 - rsi) / 30  # rsi=30->0, rsi=0->1
    elif rsi >= 70:
        score = - (rsi - 70) / 30  # rsi=70->0, rsi=100->-1
    else:
        # Between 30 and 70: linear around 50
        score = - (rsi - 50) / 20  # rsi=50->0, rsi=30->1, rsi=70->-1
    if score > 1:
        score = 1.0
    if score < -1:
        score = -1.0
    return round(score, 4)

METHOD_NAME = "rsi_oversold"
