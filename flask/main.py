from flask import Flask, render_template, request
import requests
import sys

#Tell sys to look for utils in Main Root
sys.path.append('./..')
from utils import MDB

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