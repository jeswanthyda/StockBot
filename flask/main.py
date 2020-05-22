from flask import Flask, render_template, request
import requests
import pymongo
from alpha_vantage.timeseries import TimeSeries

app = Flask(__name__)

class Stock:

    def __init__(self,stock_name,alpha_vantage_key):
        self.stock_name = stock_name
        self.ts = TimeSeries(alpha_vantage_key,output_format='pandas')

    #Any methods that perform action on the stock go here
    def updateValues(self):
        (data, meta_data) = self.ts.get_intraday(symbol=self.stock_name,interval='1min')
        currentValue = data['4. close'][-1]
        stock_value_plot = {'x_axis':list(map(str,data.index)), 'y_axis':list(data['4. close'])}
        return currentValue, stock_value_plot

    #Can write Buy, Sell methods here


class MDB:

    def __init__(self,username,password):
        self.client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority".format(username,password))
        self.db = self.client.Portfolio
        self.currentData = self.db.currentData
        self.inventory = self.db.inventory

    def get_current_values(self):
        query = {'documentID':'currentValues'}
        return self.currentData.find_one(query)
    
    def get_current_stocks(self):
        query = { 'documentID':'currentStocks' }
        return self.currentData.find_one(query)['stockSymbols']

    def get_stock_inventory(self):
        return self.inventory.find({})

#Stocks and corresponding keys
alpha_vantage_key = 'UZZYK4G5CR2JS7AZ'

database = MDB('dbuser','StockBot')
    

@app.route("/line")
def line():
    stock_price_list = []
    stock_name_list = []
    stock_value_plot_list = []
    symbols = database.get_current_stocks()
    for s in symbols:
        new_stock = Stock(s,alpha_vantage_key)
        stock_name_list.append(s)
        value,stock_value_plot = new_stock.updateValues()
        print(value,stock_value_plot)
        stock_price_list.append(value)
        stock_value_plot_list.append(stock_value_plot)
    return render_template('line.html',data=list(zip(stock_price_list,stock_name_list,stock_value_plot_list)))
    

@app.route("/")
def coverPage():
    return render_template('home.html')

@app.route("/portfolio")
def portfolio():
    current_values = database.get_current_values()
    stock_inventory = database.get_stock_inventory()
    return render_template('portfolio.html',current_values=current_values,stock_inventory=stock_inventory)
    
if __name__ == "__main__":
    app.run(debug=True)