"""Backtest Runner

Usage example:
    python backtest.py --symbols BTC,ETH --limit 300
"""
from __future__ import annotations

import argparse
import json
from core.backtester import Backtester

def parse_args():
    p = argparse.ArgumentParser(description="Run historical backtest")
    p.add_argument("--symbols", type=str, default="BTC,ETH", help="Comma separated symbols")
    p.add_argument("--limit", type=int, default=500, help="Max candles per symbol")
    return p.parse_args()

def main():
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    bt = Backtester()
    result = bt.run(symbols, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
