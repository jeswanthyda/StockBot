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

def calculate_maxBuyingCap(cash,av_stocks):
    cap = cash/av_stocks
    return cap

def calulate_profit(buying_price,selling_price,volume):
    profit = (selling_price-buying_price)*volume
    return profit

def update_currentData_buy(cash,av_stocks):
    myquery = {'documentID': 'currentValues'}
    newvalues = { "$set": { "cash":cash,
                            "av_stocks":av_stocks } }
    db.currentData.update_one(myquery, newvalues)
    return

def update_currentData_sell(cash, profit,av_stocks):
    myquery = {'documentID': 'currentValues'}
    newvalues = { "$set": { "cash":cash,
                            "profit":profit,
                            "av_stocks":av_stocks } }
    db.currentData.update_one(myquery, newvalues)
    return

def push_tradelogs(timestamp,symbol,stockvalue,action,volume=200):
    log = {
        'timeStamp': timestamp,
        'stockSymbol': symbol,
        'stockValue' : stockvalue,
        'volume' : volume,
        'action':action
    }
    x = db.tradeLogs.insert_one(log)
    return

def add_inventory(timestamp,symbol,buyvalue,currentvalue,action,volume=200):
    investment = {
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

def get_avstocks():
    stock_data = db.currentData.find_one({"documentID":"currentStocks"})
    total_stocks = len(stock_data['stockSymbols']+stock_data['carryForward']) - db.inventory.count_documents({})
    #print(total_stocks)
    return total_stocks

def remove_symbol(symbol):
    a = db.currentData.find_one({"documentID":"currentStocks"})['carryForward']
    a.remove(symbol)
    myquery = {"documentID":"currentStocks"}
    newvalues = { "$set": {'carryForward':a} }
    db.currentData.update_one(myquery, newvalues)
    db.intraday_stockval.delete_one({'index':symbol})
    return

if __name__ == "__main__":
    client = MongoClient("mongodb+srv://dbuser:StockBot@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority")
    db = client.Portfolio
    col = db.intraday_stockval
    av_stocks = get_avstocks()
    update_currentData_buy(db.currentData.find_one({'documentID': 'currentValues'})['cash'], av_stocks)
    
    while True:
        stocks = {}

        for cols in col.find():
            stocks[cols['index']]=pd.DataFrame(cols['data']).set_index('Datetime')        
        
        for sym,data in stocks.items():
            timestamp, action, stockvalue = trade_stratgy(data)
            av_stocks = get_avstocks()
            data = db.currentData.find_one({'documentID': 'currentValues'})
            max_buycap = calculate_maxBuyingCap(data['cash'],av_stocks)
            if action=="buy" and stockvalue<=max_buycap:    
                volume = int(max_buycap/stockvalue)
                buyValue = volume*stockvalue
                push_tradelogs(timestamp, sym, stockvalue, action,volume=volume)
                add_inventory(timestamp,sym,stockvalue,stockvalue,action,volume=volume)
                update_currentData_buy(data['cash']-buyValue, av_stocks-1)
                #print("Added to inventory:",sym)
            elif action=="sell":
                inv = db.inventory.find_one({'stockSymbol':sym})
                pofit = calulate_profit(inv['buyValue'],stockvalue, inv['volume'])
                push_tradelogs(timestamp, sym, stockvalue, action,volume=inv['volume'])
                cash = stockvalue*inv['volume']
                delete_inventory(sym)
                update_currentData_sell(data['cash']+cash, data['profit']+profit,av_stocks+1)
                if sym in db.currentData.find_one({"documentID":"currentStocks"})['carryForward']:
                    remove_symbol(sym)
                print("removed from inventory:",sym)
            else:
                pass

        #trigger when mongo is updated
        print("Sleep for a minute")
        time.sleep(60)