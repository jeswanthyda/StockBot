from utils import MDB,TradeStrategy
import pandas as pd
import time
from datetime import datetime
import sys
from pytz import timezone

if __name__ == "__main__":

    #Initialization
    database = MDB('dbuser','StockBot')
    trade = TradeStrategy()

    old_timestamp = 0
    new_timestamp = 1
    num_minutes = 120
    num_stocks = 10

    #Clear all data in mongoDB
    database.intraday.delete_many({})
    database.inventory.delete_many({})
    database.tradelogs.delete_many({})

    #Initialize Portfolio with 10000USD Cash
    database.initialize_portfolio(capital=10000)
    
    while True:
        timeBegin = time.time()

        #Step1 - update hot stocks - should be one line call (check for 9 am and tackling inventory has to happen in some class method)

        database.update_stocks_live(num_minutes,num_stocks)

        #Step2 - get all inventory and update current values of stocks in inventory and stock value in current data - one liner
        database.update_stock_val_inventory()
        av_stocks = database.get_avstocks()
        database.update_currentData_buy(database.currentData.find_one({'documentID': 'currentValues'})['cash'], av_stocks)
        
        #Step3 - get all stock symbols - one liner
        stocks = {}
        for cols in database.intraday.find():
            stocks[cols['index']]=pd.DataFrame(cols['data']).set_index('Datetime')        
        new_timestamp = list(stocks.values())[0].index[0]

        
        print(old_timestamp,new_timestamp)
        if trade.is_take_action(old_timestamp,new_timestamp):
            # Inside for loop
                #Step4 - generate action signal for stock - one liner
                #step5 - take corresponding action - one liner
            for sym,data in stocks.items():
                timestamp, action, stockvalue = trade.trade_stratgy(data)
                
                av_stocks = database.get_avstocks()
                data = database.currentData.find_one({'documentID': 'currentValues'})
                max_buycap = trade.calculate_maxBuyingCap(data['cash'],av_stocks)
                
                if action=="buy" and stockvalue<=max_buycap:    
                    volume = trade.get_volume(max_buycap,stockvalue)
                    trade.buy_stock(database,timestamp,sym,stockvalue,action,volume)
                
                elif action=="sell":
                    trade.sell_stock(database,timestamp,sym,stockvalue,action)
                
                else:
                    pass

        old_timestamp = new_timestamp            
        #trigger when mongo is updated
        print("Sleep for a minute")
        timeEnd = time.time()
        timeElapsed = timeEnd - timeBegin
        time.sleep(60-timeElapsed)