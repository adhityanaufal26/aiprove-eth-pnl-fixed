"""Backtester for the eth-pnl-fixed strategy.

Replays generate_positions() over bars.csv with the execution and cost
model documented in strategy.py:

  - Signal decided at close of bar i, filled at OPEN of bar i+1.
  - Fill price = next bar's open. No phantom fills: a fill only happens
    when the target actually changes, at a real traded price.
  - Cost per fill: notional * (TAKER_FEE + SLIPPAGE * |dpos| / 1 ETH)
      TAKER_FEE = 0.10% (Binance spot taker), SLIPPAGE = 0.05% at 1 ETH,
      scaling linearly with size. One full-size (1 ETH) leg therefore
      costs 0.15% of notional (~$3.00 at $2,000/ETH); a flip (-1 -> +1,
      2 ETH traded) costs ~$5.85-$7.80 depending on price.
  - Position liquidated at the close of the final bar (costed the same way).
  - Equity = cash + position * close; PnL is the final equity starting
    from 0 cash / 0 position. Max drawdown is measured on that equity curve.

Usage:
  python3 backtest.py bars.csv            # full 24h + walk-forward splits
  python3 backtest.py bars.csv --cost 25  # cost sensitivity, bps per leg
"""
import argparse
import sys

from strategy import load_bars, generate_positions

TAKER_FEE = 0.001   # 0.10% of notional traded
SLIPPAGE = 0.0005   # 0.05% of notional at 1 ETH, scaled linearly by |dpos|


def backtest(bars, positions, lo, hi, fee=TAKER_FEE, slip=SLIPPAGE):
    """Replay bars[lo:hi]. Returns dict(pnl, trades, max_drawdown, fills)."""
    cash = 0.0
    pos = 0.0
    equity = []
    fills = []
    trades = 0
    for i in range(lo, hi):
        if i > lo:
            # fill the target decided at the close of bar i-1, at bar i's open
            d = positions[i - 1] - pos
            if abs(d) > 1e-9:
                px = bars[i]["open"]
                cost = abs(d) * px * (fee + slip * abs(d))
                cash -= d * px + cost
                pos = positions[i - 1]
                trades += 1
                fills.append((i, px, pos, cost))
        equity.append(cash + pos * bars[i]["close"])
    if pos != 0.0:  # liquidate at the final close
        px = bars[hi - 1]["close"]
        cost = abs(pos) * px * (fee + slip * abs(pos))
        cash += pos * px - cost
        trades += 1
        fills.append((hi - 1, px, 0.0, cost))
        equity[-1] = cash
    peak = 0.0
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        max_dd = max(max_dd, peak - e)
    return {"pnl": equity[-1], "trades": trades,
            "max_drawdown": max_dd, "fills": fills}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bars", nargs="?", default="bars.csv")
    ap.add_argument("--cost", type=float, default=15.0,
                    help="total cost per full-size leg in bps (fee+slippage)")
    args = ap.parse_args()
    fee = args.cost / 10000.0 * (2.0 / 3.0)
    slip = args.cost / 10000.0 * (1.0 / 3.0)
    bars = load_bars(args.bars)
    positions = generate_positions(bars)
    n = len(bars)
    half = n // 2
    full = backtest(bars, positions, 0, n, fee, slip)
    first = backtest(bars, positions, 0, half, fee, slip)
    second = backtest(bars, positions, half, n, fee, slip)
    print(f"bars: {n}  cost: {args.cost:.0f} bps/leg "
          f"(fee {fee*10000:.1f} bps + slippage {slip*10000:.1f} bps at 1 ETH)")
    for label, r in [("in-sample  (bars 0-719)  ", first),
                     ("out-of-sample (bars 720-1439)", second),
                     ("full 24h   (bars 0-1439) ", full)]:
        print(f"{label}: net PnL ${r['pnl']:+8.2f}  "
              f"trades {r['trades']}  max drawdown ${r['max_drawdown']:.2f}")
    print("fills (bar, fill price, position after fill, cost):")
    for bar, px, p, c in full["fills"]:
        print(f"  bar {bar:4d}  ${px:8.2f}  pos {p:+.0f} ETH  cost ${c:.2f}")


if __name__ == "__main__":
    sys.exit(main())
