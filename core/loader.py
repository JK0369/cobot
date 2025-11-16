"""데이터 로더

과거 캔들 데이터(CSV)를 읽고, 실시간 데이터용 간단한 스텁을 제공합니다.
추후 Binance WebSocket 연동으로 확장할 수 있습니다.

CSV 포맷 (data/historical/<SYMBOL>.csv):
    timestamp,open,high,low,close,volume

반환되는 캔들 딕셔너리 키: 'timestamp','open','high','low','close','volume'
"""
from __future__ import annotations

import csv
import os
from typing import List, Dict, Optional

HISTORICAL_DIR = os.path.join("data", "historical")
LIVE_DIR = os.path.join("data", "live")

# 지원 타임프레임과 초 단위 매핑
TIMEFRAME_TO_SECONDS = {
    "5m": 5 * 60,
    "15m": 15 * 60,
    "1h": 60 * 60,
    "4h": 4 * 60 * 60,
    "1d": 24 * 60 * 60,
}

class HistoricalLoader:
    def __init__(self, directory: str = HISTORICAL_DIR):
        self.directory = directory

    def load(self, symbol: str, limit: Optional[int] = None) -> List[Dict]:
        path = os.path.join(self.directory, f"{symbol}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Historical file not found: {path}")
        candles: List[Dict] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "timestamp": int(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
        if limit is not None:
            candles = candles[-limit:]
        return candles

    def load_tf(self, symbol: str, timeframe: str, limit: Optional[int] = None) -> List[Dict]:
        """타임프레임별 CSV 로딩. 우선순위 경로:
        1) data/historical/<timeframe>/<SYMBOL>.csv
        2) data/historical/<SYMBOL>_<timeframe>.csv
        3) data/historical/<SYMBOL>.csv (마지막 폴백)
        """
        # 1) 서브폴더 방식
        path1 = os.path.join(self.directory, timeframe, f"{symbol}.csv")
        # 2) 파일명 접미사 방식
        path2 = os.path.join(self.directory, f"{symbol}_{timeframe}.csv")
        # 3) 기본 파일명(폴백)
        path3 = os.path.join(self.directory, f"{symbol}.csv")

        for path in [path1, path2, path3]:
            if os.path.exists(path):
                candles: List[Dict] = []
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        candles.append({
                            "timestamp": int(row["timestamp"]),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        })
                if limit is not None:
                    candles = candles[-limit:]
                return candles
        # 아무 것도 없으면 빈 리스트
        return []

class LiveLoader:
    """Stub for live data integration.

    In a real implementation, this would manage WebSocket subscriptions and
    cache latest candles per timeframe, updating only when new data arrives.
    For now, it can optionally read a 'latest' snapshot CSV in data/live.
    """
    def __init__(self, directory: str = LIVE_DIR):
        self.directory = directory

    def get_latest(self, symbol: str, limit: int = 100) -> List[Dict]:
        path = os.path.join(self.directory, f"{symbol}_latest.csv")
        if not os.path.exists(path):
            # 파일 없으면 빈 리스트 반환 (호출 측에서 historical 대체 가능)
            return []
        candles: List[Dict] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "timestamp": int(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
        return candles[-limit:]

    def get_latest_tf(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict]:
        """타임프레임별 최신 스냅샷 로딩. 우선순위 경로:
        1) data/live/<timeframe>/<SYMBOL>_<timeframe>_latest.csv
        2) data/live/<SYMBOL>_<timeframe>_latest.csv
        3) data/live/<SYMBOL>_latest.csv (폴백)
        """
        path1 = os.path.join(self.directory, timeframe, f"{symbol}_{timeframe}_latest.csv")
        path2 = os.path.join(self.directory, f"{symbol}_{timeframe}_latest.csv")
        path3 = os.path.join(self.directory, f"{symbol}_latest.csv")
        for path in [path1, path2, path3]:
            if os.path.exists(path):
                candles: List[Dict] = []
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        candles.append({
                            "timestamp": int(row["timestamp"]),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        })
                return candles[-limit:]
        return []


def _bucket_start(ts: int, interval: int) -> int:
    """주어진 타임스탬프 ts를 interval(초) 버킷의 시작 시각으로 내림.
    예: ts=1731000900, interval=900(15m) → 해당 15분 구간 시작 시각
    """
    return ts - (ts % interval)


def resample_candles(candles: List[Dict], timeframe: str) -> List[Dict]:
    """5분봉(또는 더 세밀한 연속 데이터)을 높은 타임프레임으로 리샘플링.

    - open: 버킷 내 첫 번째 open
    - high: 버킷 내 최대 high
    - low : 버킷 내 최소 low
    - close: 버킷 내 마지막 close
    - volume: 버킷 내 volume 합계
    """
    if timeframe not in TIMEFRAME_TO_SECONDS:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    if not candles:
        return []
    interval = TIMEFRAME_TO_SECONDS[timeframe]
    # 입력이 시간순이라고 가정하지 않고 정렬 보장
    sorted_c = sorted(candles, key=lambda x: x["timestamp"])  # oldest -> newest
    buckets: Dict[int, Dict[str, float]] = {}
    order_in_bucket: Dict[int, List[Dict]] = {}
    for c in sorted_c:
        b = _bucket_start(int(c["timestamp"]), interval)
        if b not in buckets:
            buckets[b] = {
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "volume": float(c["volume"]),
            }
            order_in_bucket[b] = [c]
        else:
            bkt = buckets[b]
            bkt["high"] = max(bkt["high"], float(c["high"]))
            bkt["low"] = min(bkt["low"], float(c["low"]))
            bkt["close"] = float(c["close"])  # 마지막 캔들의 종가로 갱신
            bkt["volume"] += float(c["volume"])
            order_in_bucket[b].append(c)
    out: List[Dict] = []
    for b_start in sorted(buckets.keys()):
        bkt = buckets[b_start]
        out.append({
            "timestamp": b_start,
            "open": bkt["open"],
            "high": bkt["high"],
            "low": bkt["low"],
            "close": bkt["close"],
            "volume": bkt["volume"],
        })
    return out


def get_multi_timeframe_candles(
    symbol: str,
    historical: Optional[HistoricalLoader] = None,
    live: Optional[LiveLoader] = None,
    timeframes: Optional[List[str]] = None,
    window: int = 300,
) -> Dict[str, List[Dict]]:
    """여러 타임프레임 캔들을 반환.

    - 각 타임프레임별로 실시간 스냅샷 → 과거 CSV 순으로 직접 로드 시도
    - 없는 타임프레임은 가장 작은(초 단위) 가용 타임프레임에서 리샘플링하여 보완
    """
    if timeframes is None:
        timeframes = ["5m", "15m"]
    if historical is None:
        historical = HistoricalLoader()
    if live is None:
        live = LiveLoader()

    # 직접 로딩 시도
    tf_data: Dict[str, List[Dict]] = {}
    for tf in timeframes:
        data_tf = live.get_latest_tf(symbol, tf, limit=window)
        if len(data_tf) < 10:
            data_tf = historical.load_tf(symbol, tf, limit=window)
        tf_data[tf] = data_tf

    # 최소 1개라도 데이터가 있어야 함. 없으면 빈 dict 반환
    available = {tf: c for tf, c in tf_data.items() if c}
    if not available:
        return tf_data

    # 가장 작은(가장 촘촘한) 타임프레임을 찾음
    smallest_tf = min(available.keys(), key=lambda t: TIMEFRAME_TO_SECONDS.get(t, 10**12))
    base = available[smallest_tf]

    # 누락된 타임프레임은 base에서 리샘플링
    for tf in timeframes:
        if tf_data.get(tf):
            continue
        tf_data[tf] = resample_candles(base, tf)
    return tf_data

__all__ = [
    "HistoricalLoader",
    "LiveLoader",
    "resample_candles",
    "get_multi_timeframe_candles",
    "TIMEFRAME_TO_SECONDS",
]
