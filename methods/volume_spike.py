"""거래량 급증(Volume Spike) 기법

가장 최근 캔들의 거래량이 과거 거래량 평균 대비 얼마나 극단적인지에 따라
점수(-1 ~ 1)를 계산합니다. 평균 대비 크게 증가하면 매수(강세) 성향의 양수,
매우 낮으면 약세로 해석하여 음수에 가깝게 매핑합니다.

함수 규약:
    compute(symbol: str, candles: list[dict]) -> float
    각 캔들 딕셔너리는 'volume' 키를 포함해야 하며 가장 최신 캔들은 candles[-1] 입니다.
"""
from __future__ import annotations

from typing import List, Dict

def compute(symbol: str, candles: List[Dict]) -> float:
    if len(candles) < 5:
        return 0.0  # 데이터가 너무 적으면 중립 점수 반환
    *previous, latest = candles
    prev_volumes = [c.get("volume", 0) for c in previous[-30:]]  # 최근 최대 30개 거래량 사용
    avg = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0
    latest_vol = latest.get("volume", 0)
    if avg <= 0:
        return 0.0
    ratio = latest_vol / avg
    # 비율을 -1..1 범위로 매핑.
    # ratio=1 -> 0 (평균 수준), ratio=2 -> 약 +0.66, ratio=3 이상은 1로 캡.
    # 평균 대비 30% 미만이면 매우 약한 상태로 간주하여 -1 부근.
    if ratio < 0.3:
        score = -1.0
    else:
        score = (ratio - 1) / 2  # ratio=1->0, ratio=3->1
    if score > 1:
        score = 1.0
    if score < -1:
        score = -1.0
    return round(score, 4)

METHOD_NAME = "volume_spike"
