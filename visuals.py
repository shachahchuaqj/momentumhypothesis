import matplotlib.pyplot as plt
import metric_calc as MC
import strategy_init as SI
import strategy_post as SP

# plot of MWR comparison against different strategies

def MWR_comparison_plot(results: dict): 
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2E7D32' if v >= 0 else '#C62828' for v in results.values()]
    ax.barh(list(results.keys()), list(results.values()), color=colors)
    ax.axvline(0, color='black', linewidth=0.8)
    ax.set_xlabel('Money-Weighted Return (%)')
    ax.set_title('Strategy Comparison: MWR over ~15-Year SPY Backtest')
    plt.tight_layout()
    plt.savefig('plots/mwr_comparison.png', dpi=150)

results = {
    'Lump Sum': 9.69,
    'DCA': 7.13,
    'Force': -0.59,
    'Force + TP': -0.00,
    'Force + TP, no SL': 0.82,
    'Force (no extreme)': -3.83,
    'Force (no opp. signs)': 2.31,
    'Momentum (k=24)': 17.31,
}




# plot of MWR against k values for momentum-only strategy

def MWR_momentum_k(k_values: list):
    mwr_values = []

    for k in k_values:
        mwr, _ = SP.momentum(10_000, k=k)
        mwr_values.append(mwr)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(k_values, mwr_values, marker='o')
    ax.axhline(9.69, color='gray', linestyle='--', label='Lump Sum benchmark')
    ax.set_xlabel('k (shares per unit change in momentum)')
    ax.set_ylabel('MWR (%)')
    ax.set_title('Momentum Strategy: Sensitivity to k')
    ax.legend()
    plt.tight_layout()
    plt.savefig('plots/k_sensitivity.png', dpi=150)

k_values = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40]




# strategy timing comparison

def plot_trade_comparison():
    stockpricesdf = SI.stockpricesdf
    firstday = SI.firstday

    initial_amount = 10_000

    _, dca_trades = SI.DCA(initial_amount, interval=21, installment=initial_amount / (SI.numdays // 21))
    _, _, mom_trades = SP.momentum(initial_amount, k=24)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(stockpricesdf['Date'], stockpricesdf['Close'], color='navy', lw=0.7, label='SPY Close', zorder=1)

    # DCA: many small, evenly-spaced buys
    dca_dates = [d for d, *_ in dca_trades]
    dca_prices = [p for *_, p in dca_trades]
    ax.scatter(dca_dates, dca_prices, color='orange', marker='o', s=15,
               label='DCA buy', zorder=2, alpha=0.6)

    # Momentum: sparse, sign-crossover-driven buys/sells
    mom_buys = [(d, p) for d, action, _, p in mom_trades if action == 'buy']
    mom_sells = [(d, p) for d, action, _, p in mom_trades if action == 'sell']
    if mom_buys:
        ax.scatter(*zip(*mom_buys), color='green', marker='^', s=25, label='Momentum buy', zorder=3)
    if mom_sells:
        ax.scatter(*zip(*mom_sells), color='red', marker='v', s=25, label='Momentum sell', zorder=3)

    # Lump sum: single trade, shown as a star
    first_price = stockpricesdf.loc[stockpricesdf['Date'] == firstday, 'Close'].iloc[0]
    ax.scatter([firstday], [first_price], color='purple', marker='*', s=150,
               label='Lump Sum buy', zorder=4)

    ax.set_title('Trade Timing Comparison: Lump Sum vs DCA vs Momentum')
    ax.set_xlabel('Date')
    ax.set_ylabel('SPY Close Price')
    ax.legend()
    plt.tight_layout()
    plt.savefig('plots/all_strategies_trades.png', dpi=150)
    plt.close(fig)




# force percentile bands plot

def pct_bands_plot(ticker: str):
    df = MC.metrics_pct(ticker)  # already has Force, Force 2.5pct, Force 97.5pct

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df['Date'], df['Force'], color='steelblue', lw=0.5, label='Force')
    ax.plot(df['Date'], df['Force 2.5pct'], color='red', lw=0.8, linestyle='--', label='2.5th/97.5th percentile bands')
    ax.plot(df['Date'], df['Force 97.5pct'], color='red', lw=0.8, linestyle='--')
    ax.set_title('Force over Time with Rolling 5-Year Percentile Bands')
    ax.legend()
    plt.tight_layout()
    plt.savefig('plots/force_bands.png', dpi=150)

pct_bands_plot('SPY')