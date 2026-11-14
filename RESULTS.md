# Backtest results — eth-pnl-fixed (Donchian 240, 1 ETH max)

Dataset: `bars.csv`, 1,440 ETH/USDT 1-min bars, 2028.68 → 1960.59
(−$68.09 drift, −3.36%). Cost model: 10 bps taker fee + 5 bps slippage
at 1 ETH = 15 bps per full-size leg. Fills at next bar's open.
Reproduce: `python3 backtest.py bars.csv`.

## Submitted strategy

| Split | Net PnL | Trades | Max drawdown |
| --- | --- | --- | --- |
| In-sample (bars 0–719) | +$1.68 | 2 | $41.35 |
| Out-of-sample (bars 720–1439) | +$66.90 | 3 | $51.99 |
| Full 24h (bars 0–1439) | **+$74.91** | 3 | $51.99 |

Benchmarks (same costs): buy-and-hold 1 ETH −$74.06 (DD $124.72); flat $0.00.

Trade log:

| Bar | Fill price | Position after | Cost | Leg PnL (gross) |
| --- | --- | --- | --- | --- |
| 4 | $2,024.61 | −1 ETH | $3.04 | — |
| 1308 | $1,948.26 | +1 ETH | $7.79 | short leg +$76.35 |
| 1439 | $1,960.59 | 0 ETH | $2.94 | long leg +$12.33 |

Gross +$88.68, costs −$13.77, net +$74.91.

## Cost sensitivity (net PnL, full 24h)

| Cost per leg | In-sample | Out-of-sample | Full |
| --- | --- | --- | --- |
| 5 bps | +$5.72 | +$76.07 | +$84.09 |
| 10 bps | +$3.70 | +$71.49 | +$79.50 |
| 15 bps | +$1.68 | +$66.90 | +$74.91 |
| 25 bps | −$2.36 | +$57.73 | +$65.73 |

Positive full-sample and out-of-sample at every cost level tested.

## Parameter plateau (net PnL, full 24h, 15 bps/leg)

| Donchian N | In-sample | Out-of-sample | Full | Trades |
| --- | --- | --- | --- | --- |
| 120 | −$92.51 | +$55.15 | −$31.59 | 9 |
| 150 | −$38.78 | +$83.01 | +$50.56 | 5 |
| 180 | −$25.17 | +$46.15 | +$26.76 | 5 |
| 210 | +$1.68 | +$66.90 | +$74.91 | 3 |
| **240** | **+$1.68** | **+$66.90** | **+$74.91** | **3** |
| 300 | +$1.68 | +$66.90 | +$74.91 | 3 |
| 360 | +$1.68 | +$66.90 | +$74.91 | 3 |

N = 210–360 give the identical trade sequence. N = 240 is mid-plateau.

## Warm-up variant (no trades before 240 bars of history)

| Donchian N | In-sample | Out-of-sample | Full | Trades |
| --- | --- | --- | --- | --- |
| 180 | −$15.43 | +$46.15 | +$36.49 | 4 |
| 240 | $0.00 | +$56.36 | +$56.36 | 3 |
| 300 | $0.00 | +$56.36 | +$56.36 | 3 |

Still positive; the submitted (no-warm-up) version's extra +$18.55 comes
from the early short entered at bar 4 on the then-available 3-bar window.
Both variants are reported here; the submitted one is the standard
Donchian definition (channel over all bars available so far).

## Candidates rejected by walk-forward (net PnL, full 24h, 15 bps/leg)

| Candidate | In-sample | Out-of-sample | Full | Trades |
| --- | --- | --- | --- | --- |
| EMA 8/21 cross | −$416.29 | −$221.64 | −$631.60 | 81 |
| EMA 12/26 cross | −$302.51 | −$43.84 | −$340.02 | 49 |
| EMA 21/55 cross | −$154.68 | +$35.97 | −$121.00 | 25 |
| EMA 21/55 + 10-bar confirm | −$92.82 | +$38.11 | −$48.95 | 17 |
| SMA 100 momentum | −$613.38 | −$68.75 | −$684.42 | 89 |
| Donchian 60 | −$55.56 | +$30.00 | −$19.79 | 13 |
| RSI 14 30/70 mean-reversion | −$4.80 | −$133.60 | −$132.63 | 5 |
| RSI 14 25/75 mean-reversion | +$37.77 | −$81.19 | −$37.65 | 5 |
| Bollinger 20/2.0 reversion | −$135.33 | −$171.13 | −$300.70 | 103 |
| Bollinger 20/2.0 trend-filtered | −$39.11 | −$38.77 | −$72.11 | 27 |

Lesson: on 1-min bars the cost per trade (~$3–$8 per leg at 1 ETH)
exceeds the per-bar noise edge of every fast rule. Only rules trading
a handful of times survive costs. RSI 25/75 is the cautionary tale for
overfitting: best in-sample (+$37.77) of any mean-reversion candidate,
worst out-of-sample (−$81.19) — it was rejected for exactly that reason.
