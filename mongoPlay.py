import pymongo
from datetime import datetime

client = pymongo.MongoClient("mongodb+srv://dbuser:StockBot@cluster0-gbfdp.mongodb.net/test?retryWrites=true&w=majority")
db = client.Portfolio

# currentValues = {
#     'capital' : 9000,
#     'cash': 5000,
#     'stock' : 4000,
#     'profit' : 1000
#     }
# query = { 'documentID':'currentValues' }
# newvalues = {'$set': currentValues}
# x = db.currentData.update_one(query,newvalues)


# currentStocks = {
#     'documentID': 'currentStocks',
#     'stockSymbols': ['IBM','UAA','AMZN','MSFT','NVDA']
# }
# query = { 'documentID':'currentStocks' }
# newvalues = {'$set': currentStocks}
# x = db.currentData.update_one(query,newvalues)


# log = {
#     'timeStamp': datetime.now(),
#     'stockSymbol': 'MSFT',
#     'stockValue' : 120.43,
#     'amount': 200,
#     'action' : 'buy',
# }
# x = db.tradeLogs.insert_one(log)


# investment = {
#     'investmentID' : 2,
#     'timeStamp': datetime.now(),
#     'stockSymbol': 'MSFT',
#     'buyValue' : 120.43,
#     'currentValue' : 120.43,
#     'volume': 200,
# }
# x = db.inventory.insert_one(investment)
# query = {'investmentID':1}
# x = db.inventory.delete_one(query)


# query = {'documentID':'currentValues'}
# x = db.currentData.find(query)
# print(x)

