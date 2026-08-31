from datetime import datetime
import pandas as pd
from scipy.optimize import brentq

import metric_calc as MC

ticker = 'SPY'          #insert a different ticker if needed
stockdf = MC.metrics(ticker)

class Account:
    def __init__(self, id: str):
        self.name = id
        self.balance = 0          #liquid cash balance
        self.log: list[tuple[datetime, float]] = []                   #log of all deposits and withdrawals, stored as a list of (date, amount)
        self.positionlist: dict[str, AssetPosition] = dict()          #list of current open positions {ticker_str: AssetPosition object}

    def __str__(self) -> str:
        return f"Account '{self.name}'; current balance '{round(self.balance,2)}'."

    def deposit(self, amount: float, date: datetime) -> None:
        self.balance += amount
        self.log.append((date.date(), -1 * amount))                     #deposit is counted as a "negative" change in investor's wallet
        print(f"{amount} deposited, current balance {self.balance}")

    def withdraw(self, amount: float, date: datetime) -> None:
        if amount > self.balance:
            raise ValueError(f"Insufficient balance. Current balance '{round(self.balance,2)}'.")
        else:
            self.balance -= amount
            self.log.append((date.date(), amount))                      #withdrawal is counted as a "positive" change in investor's wallet
            print(f"{amount} withdrawn, current balance {self.balance}")

    def PV(self, cur_pricelist: dict[str, float]) -> float:
        ''' 
        returns net present value of the entire portfolio.
        cur_pricelist is a dictionary of {ticker_str: current_price}.
        '''
        totalassetvalue = 0
        for ticker in list(self.positionlist.keys()):
            if cur_pricelist[ticker]:
                totalassetvalue += self.positionlist[ticker].net_shares * cur_pricelist[ticker]
        return self.balance + totalassetvalue

    def stop_loss(self, date: datetime, cur_pricelist: dict[str, float]) -> None:
        ''' 
        cur_pricelist is a dictionary of {ticker_str: current_price}.
        checks all AssetPosition in self.positionlist, and closes any position if the unrealised PnL is <= -50%. 
        '''
        for ticker in list(self.positionlist.keys()):
            if cur_pricelist[ticker]:
                current_price = cur_pricelist[ticker]
                position = self.positionlist[ticker]
                if position.unrealisedPnLpct(current_price) <= -50:
                    if position.isShort:
                        position.buy(abs(position.net_shares), current_price, date)
                    else:
                        position.sell(abs(position.net_shares), current_price, date)


    def closeAccount(self, date: datetime, cur_pricelist: dict[str, float]) -> float:
        ''' 
        cur_pricelist is a dictionary of {ticker_str: current_price}.
        Liquidate all positions and then close the account, finally returning the MWR. 
        '''
        for ticker in list(self.positionlist.keys()):
            if cur_pricelist[ticker]:
                current_price = cur_pricelist[ticker]
                position = self.positionlist[ticker]
                if position.isShort:
                    position.buy(abs(position.net_shares), current_price, date)
                else:
                    position.sell(abs(position.net_shares), current_price, date)
        self.withdraw(self.balance, date)
        
        return calculate_mwr(self.log)

class SingleTrade:
    def __init__(self, ticker: str, units: float, price: float, date: datetime):
        self.ticker = ticker
        self.units = units
        self.price = price
        self.date = date.date()

    def amount(self) -> float:
        return self.units * self.price

#before making any trade, must ensure that the AssetPosition is in Account.positionlist
class AssetPosition:
    def __init__(self, account: Account, ticker: str):
        self.account = account
        self.ticker = ticker
        self.net_shares = 0
        self.isShort: bool = None
        self.tradehistory: set[SingleTrade] = set()

    def buy(self, units: float, price: float, date: datetime):
        self.account.balance -= units * price
        self.net_shares += units
        if self.tradehistory == set():
            self.isShort = False
        self.tradehistory.add(SingleTrade(self.ticker, units, price, date))
        print(f"{units} shares of {self.ticker} bought at price {price} on {date.date()}")

        if self.net_shares == 0:
            #position is reset if buying when short makes net_shares == 0.
            del self.account.positionlist[self.ticker]

    def sell(self, units: float, price: float, date: datetime):
        self.account.balance += units * price
        self.net_shares -= units
        if self.tradehistory == set():
            self.isShort = True
        self.tradehistory.add(SingleTrade(self.ticker, -1 * units, price, date))
        print(f"{units} shares of {self.ticker} sold at price {price} on {date.date()}")

        if self.net_shares == 0:
            #position is reset if selling when long makes net_shares == 0.
            del self.account.positionlist[self.ticker]

    def avg_entry_price(self) -> float:
        totalcost, totalunits = 0, 0
        if not self.isShort:        #i.e. long position
            for trade in self.tradehistory:
                if trade.units > 0:
                    totalcost += trade.amount()
                    totalunits += trade.units
            return totalcost / totalunits
        else:                       #i.e. short position
            for trade in self.tradehistory:
                if trade.units < 0:
                    totalcost -= trade.amount()
                    totalunits -= trade.units
            return totalcost / totalunits

    def unrealisedPnL(self, current_price: float) -> float:
        # this works for both short and long positions
        return self.net_shares * (current_price - self.avg_entry_price())
    
    def unrealisedPnLpct(self, current_price: float) -> float:
        avgprice = self.avg_entry_price()
        return 100 * self.net_shares * (current_price - avgprice) / avgprice
        # this works for both short and long positions

def calculate_mwr(cashflow_list: list[tuple[datetime, float]]) -> float:
    '''
    cashflow_list must be a list of tuples (date of withdrawal / deposit, amount withdrawn / deposited).
    withdrawals are counted as positive, while deposits are negative.
    MWR is returned as a percentage.
    '''
    if len(cashflow_list) < 2:
        raise ValueError("Need at least two cash flows (an inflow and an outflow) to compute MWR.")

    dates = [cf[0] for cf in cashflow_list]
    amounts = [cf[1] for cf in cashflow_list]
    t0 = min(dates)

    def npv(rate: float) -> float:
        total = 0.0
        for date, amount in zip(dates, amounts):
            days = (date - t0).days
            total += amount / ((1 + rate) ** (days / 365))
        return total

    return brentq(npv, -0.9999, 10)