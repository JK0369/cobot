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

__all__ = ["HistoricalLoader", "LiveLoader"]
