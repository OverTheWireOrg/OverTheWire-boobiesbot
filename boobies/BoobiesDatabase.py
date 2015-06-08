#!/usr/bin/python

import string

class BoobiesDatabase(object):
    def isValidTag(self, tag): #{{{
	allowed = set(string.ascii_lowercase + string.digits)
        return tag.startswith("#") and set(tag[1:]) <= allowed
    #}}}
    def addBoobies(self, url, addedby=None): #{{{
    	# return id or None if failed
        return None
    #}}}
    def alreadyStored(self, url): #{{{
        # check if URL exists
	pass
    #}}}
    def getSpecificBoobies(self,id): #{{{
        # return record
	pass
    #}}}
    def getRandomBoobies(self, tags=None): #{{{
        # get a random entry
	pass
    #}}}
    def delBoobies(self, bid): #{{{
        # remove from database
	pass
    #}}}    
    def addTags(self, bid, tags, addedby=None): #{{{
    	pass
    #}}}
    def delTags(self, bid, tags): #{{{
    	pass
    #}}}
