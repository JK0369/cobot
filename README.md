# Binance Trading Bot Skeleton

직관적이고 초보자 친화적인 구조로 실시간(score/action) 계산과 동일 로직 기반 백테스트를 수행할 수 있는 파이썬 프로젝트 스켈레톤입니다.

## 폴더 구조
```
project/
  config/           # 설정 (methods + weight)
    settings.json
  core/             # 핵심 엔진 모듈
    calculator.py   # 동적 메서드 로딩 및 가중치 계산
    loader.py       # 데이터 로더 (historical + live stub)
    position.py     # score -> action 결정 로직
    backtester.py   # 백테스트 엔진
  data/
    historical/     # 과거 데이터 CSV (timestamp,open,high,low,close,volume)
    live/           # 실시간 최신 스냅샷 (옵션)
  methods/          # 분석 방법 모듈 (추가만 하면 자동 로딩)
    volume_spike.py
    rsi_oversold.py
  main.py           # 실시간(또는 데모) 실행 진입점
  backtest.py       # 백테스트 실행 진입점
  README.md
```

## 설정 (config/settings.json)
```json
[
  { "method": "volume_spike", "weight": 0.5 },
  { "method": "rsi_oversold", "weight": 0.7 }
]
```
- 새 분석 기법 추가 절차:
  1. `methods/` 폴더에 `<name>.py` 작성 (필수: `METHOD_NAME`, `compute()` 함수)
  2. `settings.json`에 `{ "method": "<METHOD_NAME>", "weight": <number> }` 추가
  3. 프로그램 재실행 → 자동 반영

## 분석 메서드 규칙
각 파일은 아래 형태를 따라야 합니다:
```python
METHOD_NAME = "example_method"

def compute(symbol: str, candles: list[dict]) -> float:
    # -1..1 사이 score 반환
    return 0.0
```
`candles` 리스트의 마지막 요소가 최신 캔들이며 필요한 키(close, volume 등)는 메서드가 자체적으로 가정합니다.

## Score 종합 로직
`core/calculator.py` 에서:
- 모든 활성화된 메서드를 동적 임포트
- `settings.json`의 weight 기반으로 가중 평균 -> 최종 score (-1..1)

## Action 결정 로직 (`core/position.py`)
단순 규칙:
- `score >= 0.4` & 미보유 → `buy`
- `score <= -0.4` & 보유 → `sell`
- 보유 중 손실 -5% 이하 → `sell`
- 그 외 → `hold`

## 실시간/데모 실행 (`main.py`)
임시로 historical 데이터를 live 대용으로 사용:
```bash
python main.py
```
출력 예시 (JSON):
```json
{
  "BTC": {"score": 0.12, "has_position": false, "entry_price": null, "current_price": 68100, "action": "hold"},
  "ETH": {"score": -0.55, "has_position": true, "entry_price": 3100, "current_price": 3065, "action": "sell"}
}
```

## 백테스트 실행 (`backtest.py`)
```bash
python backtest.py --symbols BTC,ETH --limit 300
```
출력 예시:
```json
{
  "total_trades": 12,
  "win_rate": 0.5833,
  "total_pnl": 85.5,
  "max_drawdown": -4.2,
  "trades": [
    {"symbol": "BTC", "entry_price": 68250, "exit_price": 68450, "pnl": 200, "hold_time_minutes": 30},
    ...
  ]
}
```

## CSV 포맷
`data/historical/BTC.csv` 예시:
```
timestamp,open,high,low,close,volume
1731000000,68000,68200,67900,68100,120
...
```
`timestamp`는 초 단위 Unix Epoch (분 단위도 가능)이고 backtester는 hold_time_minutes 계산 시 분 단위로 환산합니다.

## 확장 아이디어
- Binance WebSocket 연동 (`LiveLoader` 교체)
- 다양한 타임프레임 동시 계산 (5m,15m,1h 등) 후 멀티-타임프레임 가중치
- 포지션 사이징 (고정 1단위 → 비율 기반 변경)
- 수수료/슬리피지 반영
- 성능 리포트 추가 (샤프 비율, 평균 보유 시간 등)

## 빠른 시작
```bash
cd project
python backtest.py --symbols BTC,ETH --limit 200
python main.py
```

## 문제 해결 팁
- 메서드 추가 후 반영 안 되면: 경로/`METHOD_NAME` 확인 후 재실행
- score가 항상 0이면: 데이터 충분한지(캔들 수) 및 메서드 예외 확인
- 백테스트가 0 트레이드면: threshold 조정 (`BUY_THRESHOLD`, `SELL_THRESHOLD`) 또는 weight 조정

행복한 코딩 되세요! 🙂
