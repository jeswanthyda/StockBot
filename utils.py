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
        
        #Change time zone to EST
        self.from_zone = tz.gettz('UTC')
        self.to_zone = tz.gettz('America/New_York')
    
    # Ruturaj Functions that depend on MongoDB

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