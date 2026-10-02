# quant-backtester

A small **event-driven backtesting engine** for systematic strategies. It keeps the parts that most often make backtests lie explicit: order timing, fills, slippage, commissions and portfolio accounting.

## Design

- **Bar-by-bar events.** On bar *t* a strategy sees history up to the close of *t* through a `Context` and submits orders.
- **Realistic fills.** Market orders fill at the **next bar's open**; stop orders trigger only when the next bar trades through the stop (gap-aware).
- **Costs.** Slippage and commission in basis points, plus an optional minimum commission.
- **Accounting.** Cash and positions are updated from fills only; equity is marked to the close. A test checks that cash plus marked positions equals reported equity.
- **Metrics.** CAGR, volatility, Sharpe, Sortino, max drawdown, Calmar, VaR and CVaR at 95%.

## Writing a strategy

```python
from qbt import Engine, Strategy, stats, synthetic_ohlc

class Breakout(Strategy):
    def on_bar(self, ctx):
        h = ctx.history("AAA", 55)
        if len(h) == 55 and ctx.price("AAA") >= h["high"].iloc[:-1].max():
            ctx.order_target_percent("AAA", 1.0)

data = synthetic_ohlc(("AAA",))
curve = Engine(data, Breakout()).run()
print(stats(curve["equity"]))
```

## Run the examples

```bash
pip install -e ".[dev]"
python examples/run_strategies.py   # SMA cross with a protective stop, and multi-asset vol-targeted momentum
pytest
```

Results are on synthetic prices and only show that the engine works end to end.

## Tests

- Orders decided on bar *t* fill on bar *t+1* at the open, with slippage and commission applied correctly.
- Stops fill at the stop price when the bar's low passes through it.
- Changing future prices does not change past positions (no lookahead).
- The accounting identity holds at the end of a multi-asset run.
- A long-only strategy with stops never ends up short (stale stop orders are cancelled).

## License

MIT
