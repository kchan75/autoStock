from . import client

# KOSPI
def remove_kospi():
    collection = client.kstock.kospi
    return collection.remove()

def remove_kospi_by_date(datelist):
    collection = client.kstock.kospi
    for date in datelist:
        collection.remove({'date':date})

def insert_kospi(data):
    collection = client.kstock.kospi
    for num in range(len(data)):
        try:
            collection.insert(data[num])
        except:
            print("ERROR")
    return

def get_kospi(data):
    collection = client.kstock.kospi
    res_data = collection.find({"date" : { "$gte" : data }})
    return  res_data

# GOLD
def remove_gold():
    collection = client.kstock.gold
    return collection.remove()

def remove_gold_by_date(datelist):
    collection = client.kstock.gold
    for date in datelist:
        collection.remove({'date':date})

def insert_gold(data):
    collection = client.kstock.gold
    for num in range(len(data)):
        try:
            collection.insert(data[num])
        except:
            print("ERROR")
    return

def get_gold(data):
    collection = client.kstock.gold
    res_data = collection.find({"date" : { "$gte" : data }})
    return res_data

# DOLLAR
def remove_dollar():
    collection = client.kstock.dollar
    return collection.remove()

def remove_dollar_by_date(datelist):
    collection = client.kstock.dollar
    for date in datelist:
        collection.remove({'date':date})

def insert_dollar(data):
    collection = client.kstock.dollar
    for num in range(len(data)):
        try:
            collection.insert(data[num])
        except:
            print("ERROR")
    return

def get_dollar(data):
    collection = client.kstock.dollar
    res_data = collection.find({"date" : { "$gte" : data }})
    return res_data

def get_data(data):

    res_kospi = get_kospi(data)
    res_gold = get_gold(data)
    res_dollar = get_dollar(data)

    return res_kospi, res_gold, res_dollar