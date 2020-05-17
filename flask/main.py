from flask import Flask, render_template
import requests
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
        stock_value_plot = {'x_axis':list(data.index), 'y_axis':list(data['4. close'])}
        return currentValue, stock_value_plot


#Stocks and corresponding keys
alpha_vantage_key = 'UZZYK4G5CR2JS7AZ'
microsoft = Stock('MSFT',alpha_vantage_key)
    

@app.route("/")
def home():
    value,stock_value_plot = microsoft.updateValues()
    return render_template('home.html',stock_price=value,stock_name='MSFT',stock_value_plot=stock_value_plot)
    
if __name__ == "__main__":
    app.run(debug=True)