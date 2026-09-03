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

def force_noextreme(amount: float, Xshares: float, 
                use_stop_loss: bool = True, stop_loss_pct: float = -50,
                use_take_profit: bool = False, take_profit_pct: float = 10,
                account_name: str = 'Force') -> tuple[float, dict[str, int]]:
    '''
    Deposit amount into the account. 
    Now, even during non-extreme events, if "force" and "momentum" have opposite signs, buy / sell X number of shares.
    Stop-loss enforced whenever unrealised P/L drops below stop_loss_pct % (e.g. -50).
    Take-profit enforced whenever unrealised P/L goes above take_profit_pct % (e.g. 10).
    Close account and withdraw at the end of the period.
    Returns (MWR, numtrades), where MWR is a percentage and numtrades is a dict of each trade type, excluding opening and closing of the account.
    '''

    accountM = T.Account(account_name)
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    ordbuy, ordsell = 0, 0
    num_stoploss, num_takeprofit = 0, 0
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price
        
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        extreme_event = (f_val <= lower) or (f_val >= upper)
        if extreme_event:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]
            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
                ordbuy += 1
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)
                ordsell += 1

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

    return accountM.closeAccount(lastday, {ticker: last_price}), numtrades


def force_noopp(amount: float, Xshares: float, 
             use_stop_loss: bool = True, stop_loss_pct: float = -50,
             use_take_profit: bool = False, take_profit_pct: float = 10,
             account_name: str = 'Force') -> tuple[float, dict[str, int]]:
    '''
    Deposit amount into the account. 
    When "force" is below 2.5-th percentile or above 97.5-th percentile, this is considered an extreme event.
    No requirement for "force" and "momentum" to have opposite signs during an extreme event; buy if force is positive and sell if force is negative.
    Stop-loss enforced whenever unrealised P/L drops below stop_loss_pct % (e.g. -50).
    Take-profit enforced whenever unrealised P/L goes above take_profit_pct % (e.g. 10).
    Close account and withdraw at the end of the period.
    Returns (MWR, numtrades), where MWR is a percentage and numtrades is a dict of each trade type, excluding opening and closing of the account.
    '''

    accountM = T.Account(account_name)
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    ordbuy, ordsell = 0, 0
    num_stoploss, num_takeprofit = 0, 0
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price
        
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        extreme_event = (f_val <= lower) or (f_val >= upper)
        if extreme_event:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]
            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
                ordbuy += 1
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)
                ordsell += 1

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

    return accountM.closeAccount(lastday, {ticker: last_price}), numtrades


if __name__ == "__main__":
    initial_amount = 10_000

    forNE_return, forNE_tradedata = force_noextreme(initial_amount, Xshares=10, account_name='Force without extreme')
    forNO_return, forNO_tradedata = force_noopp(initial_amount, Xshares=10, account_name='Force without opposite')

    print(f"Force strategy without extreme MWR: {forNE_return:.2f}%")
    print(forNE_tradedata)
    print(f"Force strategy without opposite signs MWR: {forNO_return:.2f}%")
    print(forNO_tradedata)