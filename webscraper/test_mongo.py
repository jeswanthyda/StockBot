
import yfinance as yf

from bs4 import BeautifulSoup 
import requests
import pandas as pd
from pymongo import MongoClient

from datetime import datetime
from pytz import timezone
import time

def webscrape_companies():
    names = []
    symbols = []
    #r = requests.get('https://finance.yahoo.com/gainers')
    r = requests.get('https://finance.yahoo.com/most-active')
    soup = BeautifulSoup(r.text, "lxml")
    soup.prettify('utf-8')

    for row in soup.find_all('tr', attrs={'class': 'simpTblRow'}):
        for symbol in row.find_all('td', attrs={'aria-label':'Symbol'}):
            symbols.append(symbol.text)
        for name in row.find_all('td', attrs={'aria-label':'Name'}):
            names.append(name.text)

    est = timezone('US/Eastern')
    print("Time in EST:", datetime.now(est))

    carryForward_stocks = db.inventory.find({})
    carryforward = []
    symbols = symbols[0:num_stocks]
    for stock in carryForward_stocks :
        if stock['stockSymbol'] not in symbols:
            carryforward.append(stock['stockSymbol'])

    #print(symbols)

    currentStocks = {
        'documentID': 'currentStocks',
        'stockSymbols': symbols,
        'carryForward': carryforward,
        'timestamp': str(datetime.now(est))
    }
    query = { 'documentID':'currentStocks' }
    newvalues = {'$set': currentStocks}
    x = db.currentData.update_one(query,newvalues)
    
    #delete all documents in the collection from previous day
    db.intraday_stockval.delete_many({})

def intraday_updates(symbols, num_minutes_data, num_stocks):
    #symbols = symbols[0:num_stocks]
    est = timezone('US/Eastern')
    
    for i,symbol in enumerate(symbols):
        stock = yf.Ticker(symbol)
        #data = stock.history(period = "1d",interval = "1m")
        data = stock.history(period = "5d",interval = "1m")
        
        #reverse rows so most recent timestamp is first
        data = data.reindex(index=data.index[::-1])
        data = data.head(n=num_minutes_data)
        
        data.reset_index(inplace=True)
        data_dict = data.to_dict("records")
       
        #db.intraday_stockval.insert_one({"document_id": "stock_{}".format(i),"index":symbol,"data":data_dict})
        db.intraday_stockval.update({"document-id": "stock_{}".format(i)}, 
                                    {"document-id": "stock_{}".format(i),"index": symbol,"last-refreshed": datetime.now(est), "data": data_dict}, 
                                    upsert= True)
        
if __name__ == "__main__":
    client = MongoClient("mongodb+srv://dbuser:StockBot@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority")
    db = client.Portfolio
    num_minutes_data = 120
    num_stocks = 10
    while True:
        est = timezone('US/Eastern')
        if datetime.now(est).hour == 9:
            #schedule.run_pending()
            webscrape_companies()

        query = {'documentID':'currentStocks'}
        x = db.currentData.find_one(query)
        symbols = x['stockSymbols'] + x['carryForward']
        try:
            intraday_updates(symbols, num_minutes_data,num_stocks)
        except:
            pass
        time.sleep(60)
        