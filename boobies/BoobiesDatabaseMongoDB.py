#!/usr/bin/python

import hashlib, random, sys
from pymongo import MongoClient
from BoobiesDatabase import BoobiesDatabase

class BoobiesDatabaseMongoDB(BoobiesDatabase):
    def __init__(self, dbname = "boobies", host="localhost"): #{{{
	client = MongoClient("mongodb://%s" % host)
	db = client[dbname]
	self.collection = db[dbname]
    #}}}
    def idFromURL(self, url): #{{{
	return hashlib.sha1(url).hexdigest()[:7]
    #}}}
    def addBoobies(self, url, addedby=None): #{{{
        if self.alreadyStored(url):
	    return None

        newid = self.idFromURL(url)
        res = self.collection.insert({
	    "_id": newid,
	    "url": url,
	    "addedby": addedby,
	    "rnd": self.getRecordCount()
	})

        return newid
    #}}}
    def alreadyStored(self, url): #{{{
        return self.collection.find({"_id": self.idFromURL(url)}).count() > 0
    #}}}
    def getSpecificBoobies(self,id,tags=None): #{{{
        if id != None:
	    data = self.collection.find_one({"_id": id})
	else:
	    cnt = self.getRecordCount()
	    for i in range(50):
	    	crit = { 'rnd': { '$gte': random.randint(0, cnt - 1) } }
		if tags:
		    lctags = [x.lower() for x in tags]
		    for t in lctags:
		        if self.isValidTag(t):
			    crit["tags.%s" % t] = { "$exists": True }
			    
		data = self.collection.find_one(crit)
		if data != None:
		    break

	if data:
	    return data["url"], data["_id"], data["tags"].keys() if "tags" in data else []
	else:
	    return None, None, None

   #}}}
    def getRandomBoobies(self, tags=None): #{{{
        return self.getSpecificBoobies(None, tags)
    #}}}
    def delBoobies(self, id): #{{{
	res = self.collection.remove({"_id":id})
	print res
	return res and res["n"] > 0
    #}}}    
    def addTags(self, id, tags, addedby=None): #{{{
	lctags = [x.lower() for x in tags]
	# if tags are all valid
	if not all(self.isValidTag(x) for x in lctags):
	    return (False, "Invalid tag(s)")

        # if id exists, get record
	data = self.collection.find_one({"_id": id})

	if data:
	    if "tags" not in data:
	        data["tags"] = {}
	    
	    # add tags if they are not already there
	    data["tags"] = dict([(x, addedby) for x in lctags] + data["tags"].items())

	    res = self.collection.update({"_id": id}, data)

	    return (True, "Success")
	return (False, "Those boobies do not exist")
    #}}}
    def delTags(self, id, tags): #{{{
	lctags = [x.lower() for x in tags]
	# if tags are all valid
	if not all(self.isValidTag(x) for x in lctags):
	    return (False, "Invalid tag(s)")

        # if id exists, get record
	data = self.collection.find_one({"_id": id})

	if data and "tags" in data:
	    data["tags"] = dict((k,v) for (k,v) in data["tags"].items() if k.lower() not in lctags)
	    res = self.collection.update({"_id": id}, data)
	    return (True, "Success")
	return (False, "Those boobies or tags do not exist")
    #}}}
    def _dumpRec(self, url): #{{{
        id = self.idFromURL(url)
	return self.collection.find_one({"_id": id})
    #}}}

    def getTagNames(self, needle = None): #{{{
    	out = {}
	for i in self.collection.distinct("tags"):
	    out = dict(out.items() + i.items())
	allkeys = [x.lower() for x in out.keys()]

	if needle:
	    return [x for x in allkeys if needle.lower() in x]
	else:
	    return allkeys
    #}}}
    def getRecordCount(self): #{{{
	return self.collection.count()
    #}}}


if __name__ == '__main__':
    db = BoobiesDatabaseMongoDB()

    print db.getRecordCount()

    url = "http://test.com"
    i = db.idFromURL(url)
    print db.addBoobies(url, addedby="Steven")
    print db.alreadyStored(url)
    print db.addTags(i, ["#abc", "#x123"], addedby="Steven")
    print db.delTags(i, ["#abc"])
    print db._dumpRec(url)
    print db.getSpecificBoobies(i)
    print db.getRandomBoobies()
    print "Finding with tags:"
    print db.getRandomBoobies(["#abc"])
    print db.delBoobies(i)


