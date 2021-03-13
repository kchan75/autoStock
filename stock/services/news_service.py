from . import client

def delete_data(data):
    collection = client.kstock.news
    return collection.delete_many({'code:'. data})

def insert_data(data):
    collection = client.kstock.news
    for num in range(len(data)):
        try:
            collection.insert(data[num])
        except:
            print("ERROR")
    return

def get_data(data):
    collection = client.kstock.news
    res_data = collection.find({'code':data}, {"_id":0})
    return  res_data