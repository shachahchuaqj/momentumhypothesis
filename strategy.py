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


def DCA(amount: float, interval: int, installment: float) -> float:
    '''
    Deposit amount into the account. At every interval days, invest installment amount of money regardless of the price.
    Close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountDCA = T.Account('DCA')
    accountDCA.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

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

    return accountDCA.closeAccount(lastday, {ticker: last_price})


def momentum(amount: float, Xshares: float) -> float:
    '''
    Deposit amount into the account. 
    When "force" is below 2.5-th percentile or above 97.5-th percentile, this is considered an extreme event.
    If, during an extreme event, "force" and "momentum" have opposite signs, buy / sell X number of shares.
    Stop-loss enforced whenever unrealised P/L drops below -50%.
    Close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountM = T.Account('Momentum')
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price

        # Dividend credit/debit (works for both long and short via sign of net_shares)
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        # Signal check
        extreme_event = (f_val <= lower) or (f_val >= upper)
        opposite_signs = (m_val * f_val) < 0

        if extreme_event and opposite_signs:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]

            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)

        # Daily stop-loss check
        accountM.stop_loss(date, {ticker: price})

    return accountM.closeAccount(lastday, {ticker: last_price})


def momentum_takeprofit(amount: float, Xshares: float) -> float:
    '''
    Deposit amount into the account. 
    When "force" is below 2.5-th percentile or above 97.5-th percentile, this is considered an extreme event.
    If, during an extreme event, "force" and "momentum" have opposite signs, buy / sell X number of shares.
    Stop-loss enforced whenever unrealised P/L drops below -50%.
    Take-profit enforced whenever unrealised P/L goes above 10%.
    Close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountM = T.Account('Momentum with Take Profit')
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price

        # Dividend credit/debit (works for both long and short via sign of net_shares)
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        # Signal check
        extreme_event = (f_val <= lower) or (f_val >= upper)
        opposite_signs = (m_val * f_val) < 0

        if extreme_event and opposite_signs:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]

            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)

        # Daily stop-loss and take-profit check
        accountM.stop_loss(date, {ticker: price})
        accountM.take_profit(date, {ticker: price})

    return accountM.closeAccount(lastday, {ticker: last_price})

def momentum_takeprofit_nostoploss(amount: float, Xshares: float) -> float:
    '''
    Deposit amount into the account. 
    When "force" is below 2.5-th percentile or above 97.5-th percentile, this is considered an extreme event.
    If, during an extreme event, "force" and "momentum" have opposite signs, buy / sell X number of shares.
    Take-profit enforced whenever unrealised P/L goes above 10%.
    Close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountM = T.Account('Momentum with Take Profit and no Stop Loss')
    accountM.deposit(amount, firstday)

    div_lookup = stockdividendsdf.set_index(stockdividendsdf['ExDate'].dt.date)['Dividend']

    last_price = None
    for _, row in stockpricesdf.iterrows():
        date, price = row['Date'], row['Close']
        m_val, f_val = row['Momentum'], row['Force']
        lower, upper = row['Force 2.5pct'], row['Force 97.5pct']
        last_price = price

        # Dividend credit/debit (works for both long and short via sign of net_shares)
        if date.date() in div_lookup.index and ticker in accountM.positionlist:
            position = accountM.positionlist[ticker]
            accountM.balance += position.net_shares * div_lookup.loc[date.date()]

        # Signal check
        extreme_event = (f_val <= lower) or (f_val >= upper)
        opposite_signs = (m_val * f_val) < 0

        if extreme_event and opposite_signs:
            if ticker not in accountM.positionlist:
                accountM.positionlist[ticker] = T.AssetPosition(accountM, ticker)
            position = accountM.positionlist[ticker]

            if m_val < 0 and f_val > 0:
                position.buy(Xshares, price, date)
            elif m_val > 0 and f_val < 0:
                position.sell(Xshares, price, date)

        # Daily take-profit check
        accountM.take_profit(date, {ticker: price})

    return accountM.closeAccount(lastday, {ticker: last_price})

if __name__ == "__main__":
    initial_amount = 10_000

    ls_return = lumpsum(initial_amount)
    dca_return = DCA(initial_amount, interval=21, installment=initial_amount / (numdays // 21))
    mom_return = momentum(initial_amount, Xshares=10)
    momTP_return = momentum_takeprofit(initial_amount, Xshares=10)
    momTPNSL_return = momentum_takeprofit_nostoploss(initial_amount, Xshares=10)

    print(f"\n--- Results ---")
    print(f"Lump Sum MWR: {ls_return:.2f}%")
    print(f"DCA MWR:      {dca_return:.2f}%")
    print(f"Momentum MWR: {mom_return:.2f}%")
    print(f"Momentum with Take Profit MWR: {momTP_return:.2f}%")
    print(f"Momentum with Take Profit and No Stop Loss MWR: {momTPNSL_return:.2f}%")