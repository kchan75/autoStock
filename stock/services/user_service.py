from . import client

def get_one(query):
    collection = client.kstock.users
    data = collection.find_one((query),{"_id":0})
    return data

def insert_data(data):
    collection = client.kstock.users
    collection.insert(data)
    return