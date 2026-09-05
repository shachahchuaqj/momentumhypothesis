from datetime import datetime
import pandas as pd
import metric_calc as MC
import trading as T

ticker = 'SPY'        #insert a different ticker if needed
stockpricesdf, stockdividendsdf = MC.metrics_pct(ticker), MC._load_dividends(ticker)
numdays = len(stockpricesdf['Date'])
firstday = stockpricesdf['Date'][0]
lastday = stockpricesdf['Date'][numdays - 1]

print(stockpricesdf)
print(numdays)

def lumpsum(amount: float) -> float:
    '''
    Deposit amount into the account and buy and hold the ticker; close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountLS = T.Account('Lump Sum')
    accountLS.deposit(amount, firstday)

    first_price = stockpricesdf.loc[stockpricesdf['Date'] == firstday, 'Close'].iloc[0]
    accountLS.positionlist[ticker] = T.AssetPosition(accountLS, ticker)
    accountLS.positionlist[ticker].buy(amount / first_price, first_price, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        last_price = price

        if date.date() in div_lookup.index and ticker in accountLS.positionlist:
            position = accountLS.positionlist[ticker]
            accountLS.balance += position.net_shares * div_lookup.loc[date.date()]

    return accountLS.closeAccount(lastday, {ticker: last_price})


def DCA(amount: float, interval: int, installment: float) -> tuple[float, list[tuple[datetime, str, float, float]]]:
    '''
    Deposit amount into the account. At every interval days, invest installment amount of money regardless of the price.
    Close account and withdraw at the end of the period.
    Returns (MWR, trade_log), where 
    - MWR is a percentage;
    - trade_log is a list of trades, each as a tuple (date, 'buy/sell', shares, price).
    '''
    accountDCA = T.Account('DCA')
    accountDCA.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    trade_log = []

    last_price = None
    for i, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        last_price = price

        if date.date() in div_lookup.index and ticker in accountDCA.positionlist:
            position = accountDCA.positionlist[ticker]
            accountDCA.balance += position.net_shares * div_lookup.loc[date.date()]

        if i % interval == 0:
            if ticker not in accountDCA.positionlist:
                accountDCA.positionlist[ticker] = T.AssetPosition(accountDCA, ticker)
            accountDCA.positionlist[ticker].buy(installment / price, price, date)
            trade_log.append((date, 'buy', installment / price, price))

    return accountDCA.closeAccount(lastday, {ticker: last_price}), trade_log


def force(amount: float, Xshares: float, 
          use_stop_loss: bool = True, stop_loss_pct: float = -50,
          use_take_profit: bool = False, take_profit_pct: float = 10,
          account_name: str = 'Force') -> tuple[float, dict[str, int], list[tuple[datetime, str, float, float]]]:
    '''
    Deposit amount into the account. 
    When "force" is below 2.5-th percentile or above 97.5-th percentile, this is considered an extreme event.
    If, during an extreme event, "force" and "momentum" have opposite signs, buy / sell X number of shares.
    Stop-loss enforced whenever unrealised P/L drops below stop_loss_pct % (e.g. -50).
    Take-profit enforced whenever unrealised P/L goes above take_profit_pct % (e.g. 10).
    Close account and withdraw at the end of the period.
    Returns (MWR, numtrades, trade_log), where 
    - MWR is a percentage;
    - numtrades is a dict of each trade type, excluding opening and closing of the account;
    - trade_log is a list of trades, each as a tuple (date, 'buy/sell', shares, price).
    '''

    accountM = T.Account(account_name)
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    ordbuy, ordsell = 0, 0
    num_stoploss, num_takeprofit = 0, 0
    trade_log = []

    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price
        
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        extreme_event = (f_val <= lower) or (f_val >= upper)
        opposite_signs = (m_val * f_val) < 0
        if extreme_event and opposite_signs:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]
            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
                ordbuy += 1
                trade_log.append((date, 'buy', Xshares, price))
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)
                ordsell += 1
                trade_log.append((date, 'sell', Xshares, price))

        if use_stop_loss:
            enforced = accountM.stop_loss(date, {ticker: price}, threshold=stop_loss_pct)
            if enforced.get(ticker, False):
                num_stoploss += 1
        if use_take_profit:
            enforced = accountM.take_profit(date, {ticker: price}, threshold=take_profit_pct)
            if enforced.get(ticker, False):
                num_takeprofit += 1

    numtrades = {'Long buys executed': ordbuy,
                 'Short sells executed': ordsell,
                 'Stop losses enforced': num_stoploss,
                 'Take-profits enforced': num_takeprofit}

    return accountM.closeAccount(lastday, {ticker: last_price}), numtrades, trade_log

if __name__ == "__main__":
    initial_amount = 10_000

    ls_return = lumpsum(initial_amount)
    dca_return, _ = DCA(initial_amount, interval=21, installment=initial_amount / (numdays // 21))
    for_return, for_tradedata, _ = force(initial_amount, Xshares=10)
    forTP_return, forTP_tradedata, _ = force(initial_amount, Xshares=10, use_take_profit=True, take_profit_pct=10, account_name='Force with Take Profit')
    forTPNSL_return, forTPNSL_tradedata, _ = force(initial_amount, Xshares=10, use_take_profit=True, take_profit_pct=10, use_stop_loss=False, 
                                                   account_name='Force with Take Profit and No Stop Loss')

    print(f"\n--- Results ---")
    print(f"Lump Sum MWR: {ls_return:.2f}%")
    print(f"DCA MWR:      {dca_return:.2f}%")
    print(f"Force MWR: {for_return:.2f}%")
    print(for_tradedata)
    print(f"Force with Take Profit MWR: {forTP_return:.2f}%")
    print(forTP_tradedata)
    print(f"Force with Take Profit and No Stop Loss MWR: {forTPNSL_return:.2f}%")
    print(forTPNSL_tradedata)