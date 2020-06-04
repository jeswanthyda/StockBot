from utils import MDB,TradeStrategy
import pandas as pd
import time
from datetime import datetime
import sys
from pytz import timezone
sys.path.append('./webscraper')
from test_mongo import webscrape_companies,intraday_updates


database = MDB('dbuser','StockBot')
trade = TradeStrategy()




if __name__ == "__main__":

    while True:
        #TODO:Check time stamp for new dataframe to stop operating during off hours. 
        #TODO:Check if av_stock >0
        timeBegin = time.time()

        # TODO: Raksha - Update this part and utils
        #Step1 - update hot stocks - should be one line call (check for 9 am and tackling inventory has to happen in some class method)
        est = timezone('US/Eastern')
        if datetime.now(est).hour == 9 and datetime.now(est).minute == 0:
            webscrape_companies()
        #webscrape_companies()
        query = {'documentID':'currentStocks'}
        x = database.currentData.find_one(query)
        symbols = x['stockSymbols'] + x['carryForward']
        try:
            intraday_updates(symbols, num_minutes_data,num_stocks)
        except:
            pass

        #Step2 - get all inventory and update current values of stocks in inventory and stock value in current data - one liner
        database.update_stock_val_inventory()
        av_stocks = database.get_avstocks()
        database.update_currentData_buy(database.currentData.find_one({'documentID': 'currentValues'})['cash'], av_stocks)
        
        #Step3 - get all stock symbols - one liner
        stocks = {}
        for cols in database.intraday.find():
            stocks[cols['index']]=pd.DataFrame(cols['data']).set_index('Datetime')        
        
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

        #trigger when mongo is updated
        print("Sleep for a minute")
        timeEnd = time.time()
        timeElapsed = timeEnd - timeBegin
        time.sleep(60-timeElapsed)