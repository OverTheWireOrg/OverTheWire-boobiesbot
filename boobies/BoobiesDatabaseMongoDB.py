#!/usr/bin/python

import hashlib, random, sys
from pymongo import MongoClient
from BoobiesDatabase import BoobiesDatabase
import urllib2, base64, time

class BoobiesDatabaseMongoDB(BoobiesDatabase):
    def __init__(self, dbname = "boobies", host="localhost"): #{{{
	client = MongoClient("mongodb://%s" % host)
	db = client[dbname]
	self.collection = db[dbname]
	self.imageDataCollection = db["images"]
    #}}}
    def myHash(self, data): #{{{
	return hashlib.sha256(data).hexdigest()
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
        data = None
        if id == None:
	    allrecs = self.getAllIds(tags)
	    if len(allrecs) > 0:
		id = random.choice(allrecs)

        if id != None:
	    data = self.collection.find_one({"_id": id})

	if data:
	    return data["url"], data["_id"], self.getTags(id)
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
    def getTags(self, id): # {{{
        urlrec = self._dumpRec(id)
	if urlrec:
	    if "imgdataid" in urlrec:
		datarec = self._dumpImgData(urlrec["imgdataid"])
		if "tags" in datarec:
		    return datarec["tags"]
	    if "tags" in urlrec:
		return urlrec["tags"]
        return {}
    #}}}
    def setTags(self, id, tags): # {{{
        urlrec = self._dumpRec(id)
	if urlrec:
	    if "tags" in urlrec:
	    	urlrec["tags"] = tags
		self.collection.update({"_id": id}, urlrec, upsert=True)
		return
	    if "imgdataid" in urlrec:
		datarec = self._dumpImgData(urlrec["imgdataid"])
		if "tags" in datarec:
		    datarec["tags"] = tags
		    self.imageDataCollection.update({"_id": urlrec["imgdataid"]}, datarec, upsert=True)
		    return
        return []
    #}}}
    def addTags(self, id, tags, addedby=None): # {{{
	lctags = [x.lower() for x in tags]
	# if tags are all valid
	if not all(self.isValidTag(x) for x in lctags):
	    return (False, "Invalid tag(s)")

	if not self._dumpRec(id):
	    return (False, "Those boobies do not exist")

        # if id exists, get record
	oldtags = self.getTags(id)
	    
	# add tags if they are not already there
	newtags = dict([(x, addedby) for x in lctags] + oldtags.items())
	self.setTags(id, newtags)
	return (True, "Success")
    #}}}
    def delTags(self, id, tags): # {{{
	lctags = [x.lower() for x in tags]
	# if tags are all valid
	if not all(self.isValidTag(x) for x in lctags):
	    return (False, "Invalid tag(s)")

	if not self._dumpRec(id):
	    return (False, "Those boobies do not exist")

        # if id exists, get record
	oldtags = self.getTags(id)
	newtags = dict((k,v) for (k,v) in oldtags.items() if k.lower() not in lctags)
	self.setTags(id, newtags)
	return (True, "Success")
    #}}}
    def _dumpRec(self, id): #{{{
	return self.collection.find_one({"_id": id})
    #}}}
    def _dumpImgData(self, id): #{{{
	return self.imageDataCollection.find_one({"_id": id})
    #}}}

    def getTagNames(self, needle = None): # {{{
    	out = {}
	for i in self.collection.distinct("tags"):
	    out = dict(out.items() + i.items())
	for i in self.imageDataCollection.distinct("tags"):
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

    def getAllIds(self, tags = None): # {{{
    	# return a list of all IDs that match the given tags
	out = []
	lctags = []

	if tags:
	    lctags = [x.lower() for x in tags if self.isValidTag(x.lower())]
			
	data = self.collection.find({}, {"_id": 1})
	for rec in data:
	    addit = True
	    if tags:
	        addit = False
		realtags = self.getTags(rec["_id"])
		if all(t in realtags for t in lctags):
		    addit = True
	    if addit:
	        out += [rec["_id"]]

	return out
    #}}}
    def validateAndCacheURL(self, id, autodelete=False, updateEvery=86400): #{{{
        # for the given ID, fetch the record from mongo
	deleteme = False
	data = self._dumpRec(id)
	if data != None:
	    if not("imgdataid" in data and "lastupdate" in data and data["lastupdate"] + updateEvery > time.time()):
		try:
		    # fetch the URL
		    response = urllib2.urlopen(data["url"])
		    mimetype = response.info().getheader('Content-Type')
		    if mimetype.lower() in ["image/jpeg", "image/png", "image/gif"]:
			imgdata = response.read()
			imghash = self.myHash(imgdata)
			b64img = base64.b64encode(imgdata)

			# get the image data
			imgdatarec = self.imageDataCollection.find_one({"_id": imghash})
			if imgdatarec:
			    if "tags" in data:
				# if it exists, update the metadata and remove the metadata from URL record
				imgdatarec["tags"] = dict(imgdatarec["tags"].items() + data["tags"].items())
				del data["tags"]
			else:
			    # create the image data entry if it doesn't exist
			    imgdatarec = {
				"_id": imghash,
				"b64data": b64img,
				"tags": data["tags"] if "tags" in data else {}
			    }
			    if "tags" in data:
				del data["tags"]
			# update URL record
			data["imgdataid"] = imghash
			data["lastupdate"] = time.time()
			# write image data record (upsert)
			self.imageDataCollection.update({"_id": imghash}, imgdatarec, upsert=True)
			# write URL record (upsert)
			self.collection.update({"_id": id}, data, upsert=True)
			return
		except Exception,e: 
		    print "Found a problem: %s" % str(e)
		    deleteme = True

	    # if 404 or unknown image type, delete the URL record
	    if deleteme and autodelete:
		print "Deleting URL %s because it's faulty..." % id
		self.collection.remove({"_id": id})
	    return
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
    print db._dumpRec(i)
    print db.getSpecificBoobies(i)
    print db.getRandomBoobies()
    print "Finding with tags:"
    print db.getRandomBoobies(["#abc"])
    print db.delBoobies(i)


