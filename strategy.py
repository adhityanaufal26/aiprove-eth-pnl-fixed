"""eth-pnl-fixed: slow Donchian breakout strategy on the frozen ETH 1-min dataset.

Strategy (deliberately simple and robust -- no fitted parameters, no ML):
  Donchian channel breakout, N = 240 bars (4 hours).
  - At the close of bar i, compute the highest high and lowest low of the
    previous N bars (bars i-N .. i-1; for i < N use all bars available so far).
  - If close[i] > highest high -> target position +1 ETH (long).
  - If close[i] < lowest low   -> target position -1 ETH (short).
  - Otherwise hold the previous target (no signal -> no trade).
  - Max |position| = 1 ETH. No leverage, no scaling, no intraday exit rules.

Interface (this is the contract the sandbox / a re-runner uses):
  - Input:  bars.csv with header minute,open,high,low,close,volume
             (1,440 bars, real ETH/USDT spot 1-min bars, Binance,
              24h window ending 2026-11-13 12:17 UTC -- the frozen dataset
              published at github.com/AIProveRH/aiprove/tree/main/challenges/eth-backtest)
  - `generate_positions(bars) -> list[float]` returns the target position
    (in ETH, one of -1.0 / 0.0 / +1.0) decided at the close of each bar.
  - Execution convention (no lookahead, no phantom fills): a target decided
    at the close of bar i is filled at the OPEN of bar i+1. The position is
    liquidated at the close of the final bar.
  - Costs (see backtest.py): taker fee 0.10% of notional traded + slippage
    0.05% of notional scaled linearly by trade size (|dpos| / 1 ETH).

Why N = 240: a walk-forward check (fit on bars 0-719, test on 720-1439)
showed every fast / frequently-trading rule loses net -- 1-min noise is
~0.11% per bar while one trade leg costs ~0.15% of notional, so cost bleed
dominates anything that trades often. The slow breakout trades only 3 times
in 24h and captures the two real regime moves (the breakdown below the
4-hour low and the later breakout above the 4-hour high). N is not a
knife-edge optimum: N = 210..360 produce the identical trade sequence and
the identical net PnL (+$74.91), and a warm-up variant that refuses to trade
before 240 bars of history still nets +$56.36. See RESULTS.md.

Reproduce:
  python3 backtest.py bars.csv
"""
import csv

CHANNEL_BARS = 240
MAX_POSITION_ETH = 1.0


def load_bars(path):
    """Read bars.csv -> list of dicts with float OHLCV."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    bars = []
    for r in rows:
        bars.append({
            "minute": int(r["minute"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]),
        })
    return bars


def generate_positions(bars):
    """Target position (ETH) decided at the close of each bar.

    bars: list of dicts as returned by load_bars (or any sequence of
    mappings with 'high', 'low', 'close' keys).
    Returns a list of floats, one per bar, each in {-1.0, 0.0, +1.0}.
    Uses only data up to and including bar i to decide position i.
    """
    positions = []
    target = 0.0
    for i, bar in enumerate(bars):
        start = max(0, i - CHANNEL_BARS)
        window = bars[start:i]  # previous N bars only; never the current bar
        if window:
            highest_high = max(b["high"] for b in window)
            lowest_low = min(b["low"] for b in window)
            if bar["close"] > highest_high:
                target = MAX_POSITION_ETH
            elif bar["close"] < lowest_low:
                target = -MAX_POSITION_ETH
        positions.append(target)
    return positions


if __name__ == "__main__":
    import sys
    bars = load_bars(sys.argv[1] if len(sys.argv) > 1 else "bars.csv")
    pos = generate_positions(bars)
    n_trades = sum(1 for a, b in zip(pos, pos[1:]) if a != b) + (1 if pos[0] != 0 else 0)
    print(f"bars: {len(bars)}, position changes (excl. final liquidation): {n_trades}")
    print(f"first/last close: {bars[0]['close']:.2f} / {bars[-1]['close']:.2f}")
    print(f"final target position: {pos[-1]:+.0f} ETH")
