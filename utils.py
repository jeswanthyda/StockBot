import pymongo
from datetime import datetime
from dateutil import tz
import pandas as pd 
import numpy as np
import time
from pytz import timezone
import sys
sys.path.append('./webscraper')
from test_mongo import webscrape_companies,intraday_updates

"""
All the classes and required methods go here
"""

class MDB:

    """
    All operations that use MongoDB go under this class
    """

    def __init__(self,username,password): #Authorize with username and password while initializing
        client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority".format(username,password))
        self.db = client.Portfolio

        #Create handles for collections here
        self.currentData = self.db.currentData
        self.inventory = self.db.inventory
        self.intraday = self.db.intraday_stockval
        self.tradelogs = self.db.tradeLogs
        #Change time zone to EST
        self.from_zone = tz.gettz('UTC')
        self.to_zone = tz.gettz('America/New_York')
        #Initial Portfolio

    def initialize_portfolio(self,capital):
        myquery = {'documentID': 'currentValues'}
        newvalues = { "$set": { "cash":capital,
                                "capital":capital,
                                "stock":0,
                                'profit':0 } }
        self.currentData.update_one(myquery, newvalues)
    
    # Ruturaj Functions that depend on MongoDB

    def update_currentData_buy(self,cash,av_stocks):
        myquery = {'documentID': 'currentValues'}
        newvalues = { "$set": { "cash":cash,
                                "av_stocks":av_stocks } }
        self.currentData.update_one(myquery, newvalues)
        return

    def update_currentData_sell(self,cash, profit,av_stocks):
        myquery = {'documentID': 'currentValues'}
        newvalues = { "$set": { "cash":cash,
                                "profit":profit,
                                "av_stocks":av_stocks } }
        self.currentData.update_one(myquery, newvalues)
        return
    
    def push_tradelogs(self,timestamp,symbol,stockvalue,action,volume):
        log = {
            'timeStamp': timestamp,
            'stockSymbol': symbol,
            'stockValue' : stockvalue,
            'volume' : volume,
            'action':action
        }
        x = self.tradelogs.insert_one(log)
        # print('check:',symbol,action)
        return
    
    def add_inventory(self,timestamp,symbol,buyvalue,currentvalue,action,volume):
        investment = {
            'timeStamp': timestamp,
            'stockSymbol': symbol,
            'buyValue' : buyvalue,
            'currentValue' : currentvalue,
            'volume': volume,
        }
        x = self.inventory.insert_one(investment)
        return
    
    def delete_inventory(self,symbol):
        query = {'stockSymbol':symbol}
        x = self.inventory.delete_one(query)
        return

    def get_avstocks(self):
        stock_data = self.currentData.find_one({"documentID":"currentStocks"})
        total_stocks = len(stock_data['stockSymbols']+stock_data['carryForward']) - self.inventory.count_documents({})
        #print(total_stocks)
        return total_stocks

    def remove_symbol(self,symbol):
        a = self.currentData.find_one({"documentID":"currentStocks"})['carryForward']
        a.remove(symbol)
        myquery = {"documentID":"currentStocks"}
        newvalues = { "$set": {'carryForward':a} }
        self.currentData.update_one(myquery, newvalues)
        self.intraday.delete_one({'index':symbol})
        return

    # Raksha Functions that depend on MongoDB

    def get_allstocks(self):
        query = {'documentID':'currentStocks'}
        x = self.currentData.find_one(query)
        symbols = x['stockSymbols'] + x['carryForward']
        return symbols

    def update_stocks_live(self,num_minutes_data,num_stocks):
        est = timezone('US/Eastern')
        if datetime.now(est).hour == 9 and datetime.now(est).minute == 0:
            print('here 9')
            webscrape_companies(self.db,num_stocks)
        #webscrape_companies()
        symbols = self.get_allstocks()
        try:
            intraday_updates(self.db, symbols, num_minutes_data)
        except:
            pass

    # Jeswanth Functions that depend on MongoDB
    def get_current_values(self):
        query = {'documentID':'currentValues'}
        return self.currentData.find_one(query)
    
    def get_current_stocks(self):
        query = { 'documentID':'currentStocks' }
        return self.currentData.find_one(query)['stockSymbols']

    def get_stock_inventory(self):
        return self.inventory.find({})

    def get_intraday_plot(self):
        stocks = self.intraday.find({})
        stock_names = []
        stock_timestamp_price = []

        for s in stocks:
            stock_names.append(s['index'])
            instance_time = []
            instance_price = []
            for instance in s['data']:
                timestamp = instance['Datetime'].replace(tzinfo=self.from_zone)
                instance_time.append(timestamp.astimezone(self.to_zone))
                instance_price.append(instance['Close'])
            stock_timestamp_price.append({'x_axis':list(map(str,instance_time[::-1])), 'y_axis':list(instance_price[::-1])})
        
        return stock_names,stock_timestamp_price
    
    


    def update_stock_val_inventory(self):
        symb_vol = [(col['stockSymbol'],col['volume']) for col in self.inventory.find()]
        stock_val = 0
        for (symbol,volume) in symb_vol:
            s = self.intraday.find_one({'index':symbol})
            stock_val += s['data'][0]['Close']*volume
            query = {'stockSymbol':s}
            newvalues = { "$set": {"currentValue":s['data'][0]['Close']} }
            self.inventory.update_one(query, newvalues)
        query = {'documentID':'currentValues'}
        newvalues = { "$set": {"stock":stock_val} }
        self.currentData.update_one(query,newvalues)
        return


class TradeStrategy:

    def __init__(self):
        pass
    
    def is_take_action(self,old_timestamp,new_timestamp):
        if old_timestamp == new_timestamp:
            return True
        return False

    def trade_stratgy(self,df,short_window=15,long_window=60):
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
        # print(timestamp, action, stockvalue)
        return timestamp, action, stockvalue

    def calculate_maxBuyingCap(self,cash,av_stocks):
        if av_stocks>0:
            cap = cash/av_stocks
            return cap
        return 0

    def calulate_profit(self,buying_price,selling_price,volume):
        profit = (selling_price-buying_price)*volume
        return profit
    
    def get_volume(self,max_buycap,stockvalue):
        volume = int(max_buycap/stockvalue)
        return volume

    def buy_stock(self,database,timestamp,sym,stockvalue,action,volume):
        data = database.currentData.find_one({'documentID': 'currentValues'})
        av_stocks = database.get_avstocks()
        buyValue = volume*stockvalue
        database.push_tradelogs(timestamp, sym, stockvalue, action,volume)
        database.add_inventory(timestamp,sym,stockvalue,stockvalue,action,volume)
        database.update_currentData_buy(data['cash']-buyValue, av_stocks-1)
        #print("Added to inventory:",sym)
        return 
    
    def sell_stock(self,database,timestamp,sym,stockvalue,action):
        inv = database.inventory.find_one({'stockSymbol':sym})
        data = database.currentData.find_one({'documentID': 'currentValues'})
        av_stocks = database.get_avstocks()
        profit = self.calulate_profit(inv['buyValue'],stockvalue, inv['volume'])
        database.push_tradelogs(timestamp, sym, stockvalue, action, inv['volume'])
        cash = stockvalue*inv['volume']
        database.delete_inventory(sym)
        database.update_currentData_sell(data['cash']+cash, data['profit']+profit, av_stocks+1)
        if sym in database.currentData.find_one({"documentID":"currentStocks"})['carryForward']:
            database.remove_symbol(sym)
        print("removed from inventory:",sym)
        return
