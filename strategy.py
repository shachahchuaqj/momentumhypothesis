import pandas as pd
import metric_calc as MC
import trading as T

ticker = 'SPY'        #insert a different ticker if needed
stockpricesdf, stockdividendsdf = MC.metrics(ticker), MC._load_dividends(ticker)
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
    pass

def DCA(amount: float, interval: int, installment: float) -> float:
    '''
    Deposit amount into the account. At every interval days, invest installment amount of money regardless of the price.
    Close account and withdraw at the end of the period.
    Returns the MWR of the strategy as a percentage.
    '''
    accountDCA = T.Account('DCA')
    accountDCA.deposit(amount, firstday)
    pass

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
    pass