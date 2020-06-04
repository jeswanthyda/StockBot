from utils import MDB,TradeStrategy

database = MDB('dbuser','StockBot')

if __name__ == "__main__":
    while True:
        #Step1 - update hot stocks - should be one line call (check for 9 am and tackling inventory has to happen in some class method)
        #Step2 - get all inventory and update current values of stocks in inventory and stock value in current data - one liner
        database.update_stock_val_inventory()
        #Step3 - get all stock symbols - one liner
        # Inside for loop
            #Step4 - generate action signal for stock - one liner
            #step5 - take corresponding action - one liner
            pass