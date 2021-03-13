from . import client

def remove_data():
    collection = client.kstock.investment
    return collection.remove()

def delete_data(data):
    collection = client.kstock.investment
    return collection.delete_many({'code:'. data})

def insert_data(data):
    collection = client.kstock.investment
    for num in range(len(data)):
        try:
            collection.insert(data[num])
        except:
            print("ERROR")
    return

def get_data(data):
    collection = client.kstock.investment
    res_data = collection.find({'code':data}, {"_id":0, "code":0})
    return  res_data

def get_after_data(data):
    collection = client.kstock.investment
    res_data = collection.find({"time" : { "$gt" : data }}).sort("time")
    return res_data

def get_lasttime():
    collection = client.kstock.investment
    res_data = collection.find_one(sort=([('time', -1)]))
    # res_data = collection.find({"_id":0, "time":0})
    return res_data
