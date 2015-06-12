#!/usr/bin/python

from pymongo import MongoClient

host = "localhost"
dbname = "boobies"

client = MongoClient("mongodb://%s" % host)
db = client[dbname]
collection = db[dbname]

counter = 0
for rec in collection.find():
    i = rec["_id"]
    rec["rnd"] = counter
    collection.update({"_id": i}, rec)
    counter += 1
    print rec
