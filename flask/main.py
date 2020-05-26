from flask import Flask, render_template, request
import requests
import pymongo
from datetime import datetime
from dateutil import tz

# from alpha_vantage.timeseries import TimeSeries


app = Flask(__name__)

#TODO: Modify according to buy/sell
# class Stock:

#     def __init__(self,stock_name,alpha_vantage_key):
#         self.stock_name = stock_name
#         self.ts = TimeSeries(alpha_vantage_key,output_format='pandas')

#     #Any methods that perform action on the stock go here
#     def updateValues(self):
#         (data, meta_data) = self.ts.get_intraday(symbol=self.stock_name,interval='1min')
#         currentValue = data['4. close'][-1]
#         stock_value_plot = {'x_axis':list(map(str,data.index)), 'y_axis':list(data['4. close'])}
#         return currentValue, stock_value_plot

#     #Can write Buy, Sell methods here


class MDB:

    def __init__(self,username,password):
        self.client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority".format(username,password))
        self.db = self.client.Portfolio
        self.currentData = self.db.currentData
        self.inventory = self.db.inventory
        self.intraday = self.db.intraday_stockval
        
        self.from_zone = tz.gettz('UTC')
        self.to_zone = tz.gettz('America/New_York')

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

database = MDB('dbuser','StockBot')
    

@app.route("/line")
def line():
    stock_name_list,stock_value_plot_list = database.get_intraday_plot()
    return render_template('line.html',data=list(zip(stock_name_list,stock_value_plot_list)))
    

@app.route("/")
def coverPage():
    return render_template('home.html')

@app.route("/portfolio")
def portfolio():
    current_values = database.get_current_values()
    stock_inventory = database.get_stock_inventory()
    return render_template('portfolio.html',current_values=current_values,stock_inventory=stock_inventory)
    
if __name__ == "__main__":
    app.run()