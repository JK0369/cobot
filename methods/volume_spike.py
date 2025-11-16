"""거래량 급증(Volume Spike) 기법 (20배 기준)

최근 30개 이전 봉의 평균 거래량 대비 현재 봉 거래량 비율(ratio)을 계산합니다.
- ratio >= 20 → 강한 급증으로 간주하여 점수 1
- 1 <= ratio < 20 → (1~20) 구간을 0~1 선형 스케일
- ratio < 1 → 평균 이하이므로 0 ~ -1 범위 (ratio=0 → -1)
반환 범위: -1 ~ 1
"""
from __future__ import annotations
from typing import List, Dict

METHOD_NAME = "volume_spike"

def compute(symbol: str, candles: List[Dict]) -> float:
    # 최소 10개 이상 있어야 의미 있는 평균
    if len(candles) < 11:
        return 0.0
    *previous, latest = candles
    prev_slice = previous[-30:]  # 최근 최대 30개
    vols = [float(c.get("volume", 0)) for c in prev_slice if c.get("volume") is not None]
    if not vols:
        return 0.0
    avg = sum(vols) / len(vols)
    if avg <= 0:
        return 0.0

    current_vol = float(latest.get("volume", 0))
    ratio = current_vol / avg if avg > 0 else 0.0

    if ratio >= 20:
        score = 1.0
    elif ratio >= 1:
        # (1~20) → (0~1) 선형
        score = (ratio - 1) / (20 - 1)  # 19로 나눔
    else:
        # (0~1) → ( -1 ~ 0 ) 선형: ratio=1 →0, ratio=0 → -1
        score = -(1 - ratio)

    # 클리핑 및 반올림
    if score > 1:
        score = 1.0
    if score < -1:
        score = -1.0
    return round(float(score), 4)
