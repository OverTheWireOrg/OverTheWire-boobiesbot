#!/usr/bin/python

import hashlib, random
from pymongo import MongoClient
from BoobiesDatabase import BoobiesDatabase

class BoobiesDatabaseMongoDB(BoobiesDatabase):
    def __init__(self, dbname = "boobies"): #{{{
	client = MongoClient()
	db = client[dbname]
	self.collection = db[dbname]
    #}}}
    def idFromURL(self, url): #{{{
	return hashlib.sha1(url).hexdigest()[:7]
    #}}}
    def addBoobies(self, url): #{{{
        if self.alreadyStored(url):
	    return None

        newid = self.idFromURL(url)
        res = self.collection.insert({
	    "_id": newid,
	    "url": url,
	    "rnd": random.random()
	})

        return newid
    #}}}
    def alreadyStored(self, url): #{{{
        return self.collection.find({"_id": self.idFromURL(url)}).count() > 0
    #}}}
    def getSpecificBoobies(self,id): #{{{
        if id != None:
	    data = self.collection.find_one({"_id": id})
	else:
	    for i in range(50):
		data = self.collection.find_one({ 'rnd': { '$gte': random.random() } })
		if data != None:
		    break

	if data:
	    return data["url"], data["_id"]
	else:
	    return None, None

   #}}}
    def getRandomBoobies(self): #{{{
        return self.getSpecificBoobies(None)
    #}}}
    def delBoobies(self, id): #{{{
        if self.alreadyStored(id):
	    self.collection.remove({"_id":id})

    #}}}    


if __name__ == '__main__':
    db = BoobiesDatabaseMongoDB()

    url = "http://test.com"
    i = db.idFromURL(url)
    print db.addBoobies(url)
    print db.alreadyStored(url)
    print db.getSpecificBoobies(i)
    print db.getRandomBoobies()
    print db.delBoobies(i)


