from pymongo import MongoClient
import pandas as pd 
import numpy as np
import time
from datetime import datetime
from dateutil import tz

def trade_stratgy(df,short_window=15,long_window=60):
    short_window = short_window
    long_window = long_window
    
    df= df.reindex(index=df.index[::-1])
    # Initialize the `signals` DataFrame with the `signal` column
    df['signal'] = 0.0

    # Create short simple moving average over the short window
    df['short_mavg'] = df['Close'].rolling(window=short_window, min_periods=1, center=False).mean()

    # Create long simple moving average over the long window
    df['long_mavg'] = df['Close'].rolling(window=long_window, min_periods=1, center=False).mean()

    # Create signals
    df['signal'][short_window:] = np.where(df['short_mavg'][short_window:] 
                                                > df['long_mavg'][short_window:], 1.0, 0.0)   

    # Generate trading orders
    df['positions'] = df['signal'].diff()

    # Print `signals`
    #print(df)
    pos = df.iloc[-1,:]['positions']
    if pos==1:
        action = "buy"
    elif pos==-1:
        action = "sell"
    else:
        action = "nothing"
    
    #print(action)
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')
    timestamp = df.index[-1]
    timestamp = timestamp.replace(tzinfo=from_zone)
    timestamp = timestamp.astimezone(to_zone)
    #print(timestamp)

    stockvalue = df.iloc[-1,:]['Close']
    
    return timestamp, action, stockvalue

def push_tradelogs(timestamp,symbol,stockvalue,action,amount=200):
    log = {
        'timeStamp': timestamp,
        'stockSymbol': symbol,
        'stockValue' : stockvalue,
        'amount': amount,
        'action' : action,
    }
    x = db.tradeLogs.insert_one(log)
    return

def add_inventory(timestamp,symbol,buyvalue,currentvalue,action,volume=200):
    investment = {
        'investmentID' : 2,
        'timeStamp': timestamp,
        'stockSymbol': symbol,
        'buyValue' : buyvalue,
        'currentValue' : currentvalue,
        'volume': volume,
    }
    x = db.inventory.insert_one(investment)
    return

def delete_inventory(symbol):
    query = {'stockSymbol':symbol}
    x = db.inventory.delete_one(query)
    return

if __name__ == "__main__":
    client = MongoClient("mongodb+srv://dbuser:StockBot@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority")
    db = client.Portfolio
    col = db.intraday_stockval
    while True:
        stocks = {}
        buy_signals = {}
        sell_signals = {}
        for cols in col.find():
            stocks[cols['index']]=pd.DataFrame(cols['data']).set_index('Datetime')
        for sym,data in stocks.items():
            timestamp, action, stockvalue = trade_stratgy(data)
            if action=="buy":
                push_tradelogs(timestamp, sym, stockvalue, action,amount=200)
                add_inventory(timestamp,sym,stockvalue,stockvalue,action,volume=200)
                print("Added to inventory:",sym)
            elif action=="sell":
                push_tradelogs(timestamp, sym, stockvalue, action,amount=200)
                delete_inventory(sym)
                print("removed from inventory:",sym)
            else:
                pass
            
        #trigger when mongo is updated
        time.sleep(60)