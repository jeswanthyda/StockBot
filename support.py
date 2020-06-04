from utils import MDB,TradeStrategy
import pandas as pd
import time

database = MDB('dbuser','StockBot')
trade = TradeStrategy()

if __name__ == "__main__":
    while True:
        #Step1 - update hot stocks - should be one line call (check for 9 am and tackling inventory has to happen in some class method)
        

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
        time.sleep(60)