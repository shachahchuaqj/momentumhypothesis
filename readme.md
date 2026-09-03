A simple investigation to see if stock prices behave similarly to classical mechanics, and if a strategy based on this hypothesis is useful.

## Definitions

Let "displacement" be analogous to the current price of the stock, $P(t)$.
Then "velocity" is analogous to the daily change in the price, $\Delta P(t)$.
Suppose also that "mass" is analogous to the volume of the stock being traded, $V(t)$.
Then "momentum" would be like $V(t) \times \Delta P(t)$.

However, I want to investigate when sharp changes in the "momentum" can happen, hence these changes to the metrics should be made:
Let the volume ratio $v(t)$ be the ratio of the 5-day average volume against the 8-week daily average volume, multiplied by 100.
Then also let the growth rate $r(t) = \frac{1}{5} \frac{P(t) - P(t - 5)}{P(t - 5)} \times 100$; i.e. the simple average % growth of the stock price in the last 5-days.
Then the momentum of the stock is defined as $m(t) = v(t) r(t) \times \frac{1}{100}$, and the "force" of the stock is $f(t) = \Delta m(t)$.

## Strategy

I want to investigate if it is a good time to enter / exit the market when $f(t)$ is below the 2.5-th percentile or above the 97.5-th percentile (based on data from the 5 years before $t$), and $m(t)$ has the opposite sign of $f(t)$.
When $m(t)$ is negative but $f(t)$ is positive, this is a buy signal and we increase the "net position" by some fixed amount. If the signs are reversed, then that is a sell signal and we decrease the "net position" by that same fixed amount. Positions can be accumulated. Net position is not subject to a maximum holding period. Simultaneous long and short positions in the same asset is not allowed.

Furthermore, a stop-loss rule applies: the cost basis of the position is tracked as the volume-weighted average entry price across all accumulated trades. At the end of each trading day, if the position's unrealized P/L relative to this cost basis is ≤ −50%, the entire position is closed at the current price and the strategy resets to flat. The strategy may re-enter on a subsequent signal as normal.

## Methodology

This strategy will be compared against dollar-cost averaging (e.g. buying a certain amount of the stock at regular intervals) and simply putting a lump sum at the start to see if it is more profitable.

I will first use SPY over a 20-year period to do the comparison. Whatever positions that remain at the end of the 20 years are automatically closed at the present price, and the rate of return will be computed as the Money-Weighted Return. Dividends will be accounted for, but transaction costs and margin requirements are ignored.

## Technical Notes

`fetch_data.py` uses the module `yfinance` to get the data. If `yfinance` is unavailable, then the data should be saved as such:

Dividends: In a csv file named `dividends_{ticker}`, column A should be labelled `ExDate` and column B `Dividend`. Use `dt.strftime("%Y-%m-%d")` to convert the dates correctly. Save the csv file under the folder dividendsdata.

Prices: in a csv file named `prices_{ticker}`, columns A,B,C should be labelled `Date`, `Close`, and `Volume`. Again use `dt.strftime("%Y-%m-%d")` to convert the dates correctly. Save the csv file under the folder rawpricesdata.

## Preliminary Results

An initial amount of 10,000 was deposited into all accounts. For DCA, the 10,000 was invested in equal amounts every 21 trading days.
For the force strategy, 10 shares are bought / sold whenever an "extreme" event occured. The stop-loss was set at -50% unrealised P/L.
A take-profit modification was also tested, where if the unrealised P/L went above 10%, then the position is closed.

```
--- Results ---
Lump Sum MWR: 9.69%
DCA MWR:      7.13%
Force MWR: -0.59%
{'Long buys executed': 65, 'Short sells executed': 23, 'Stop losses enforced': 22, 'Take-profits enforced': 0}
Force with Take Profit MWR: -0.00%
{'Long buys executed': 65, 'Short sells executed': 23, 'Stop losses enforced': 15, 'Take-profits enforced': 52}
Force with Take Profit and No Stop Loss MWR: 0.82%
{'Long buys executed': 65, 'Short sells executed': 23, 'Stop losses enforced': 0, 'Take-profits enforced': 48}
```

Interestingly, trading on these extreme events alone seemed to perform way worse than DCA or even just simply buying and holding a lump sum. The best of the "force" strategies was to implement take-profit but not enforce any stop-loss; even then, the MWR was only 0.82%.
Of course, the thresholds for the stop-loss and take-profit, as well as how many shares are bought/sold during an extreme event can be varied to find an "optimal" strategy, but this still seems insufficient to fix the huge discrepancy with the "lazier" yet more profitable approaches.

Another two strategies were then tested: one where only the requirement that an extreme event must occur is dropped, and another where only the requirement that the signs of the "force" and "momentum" are opposite is dropped. Specifically for the latter, a long buy is executed if the "force" is positive, and a short sell if the "force" is negative. In neither is take-profits enabled.

```
--- Results ---
Force strategy without extreme MWR: -3.83%
{'Long buys executed': 768, 'Short sells executed': 1323, 'Stop losses enforced': 205, 'Take-profits enforced': 0}
Force strategy without opposite signs MWR: 2.31%
{'Long buys executed': 144, 'Short sells executed': 142, 'Stop losses enforced': 15, 'Take-profits enforced': 0}
```

So now it seems that just purely looking at the direction of the force, rather than requiring that it have opposite signs with the momentum, is much better (although still nowhere near DCA). Over-enforcing the force-momentum trades without the need for extremity, on the other hand, led to way more stop-losses and a much worse MWR.
