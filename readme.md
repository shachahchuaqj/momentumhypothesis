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

An initial test saw the lump sum strategy have an MWR of 9.69%, DCA strategy with 7.13%, and momentum strategy with an abysmal -0.59%. The main problem with the momentum strategy was that too many times, a large long position was accumulated but held until an "extreme" selloff took place, in which all of the gains from the long were wiped out when stop-loss was enforced.

A new strategy, "momentum with take profit" is then devised, where the position is entirely closed if the unrealised P/L exceeds 10%. Interestingly, this led to an MWR of just under -0.00%, and the profits were taken way too many times.

The stop-loss limit is then tightened from -50% to -5%. The results are still abysmal with momentum having an MWR of -0.04% and momentum with take profit having an MWR of 0.07%.