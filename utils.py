import pymongo
from datetime import datetime
from dateutil import tz

"""
All the classes and required methods go here
"""

class MDB:

    """
    All operations that use MongoDB go under this class
    """

    def __init__(self,username,password): #Authorize with username and password while initializing
        client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority".format(username,password))
        db = client.Portfolio

        #Create handles for collections here
        self.currentData = db.currentData
        self.inventory = db.inventory
        self.intraday = db.intraday_stockval
        self.tradelogs = db.tradeLogs
        #Change time zone to EST
        self.from_zone = tz.gettz('UTC')
        self.to_zone = tz.gettz('America/New_York')
    
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


class TradeStrategy:

    def __init__(self):
        pass

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
        
        return timestamp, action, stockvalue

    def calculate_maxBuyingCap(self,cash,av_stocks):
        cap = cash/av_stocks
        return cap

    def calulate_profit(self,buying_price,selling_price,volume):
        profit = (selling_price-buying_price)*volume
        return profit
