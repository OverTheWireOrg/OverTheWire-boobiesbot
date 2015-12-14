#!/usr/bin/python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import urllib2
from cStringIO import StringIO

# system imports
import sys, os.path, re
from time import gmtime, strftime

from irc.GenericIRCBot import GenericIRCBot, GenericIRCBotFactory, log
from boobies.BoobiesClassifier import isBoobiesPicture
from boobies.BoobiesDatabaseMongoDB import *

FULLNAME = "BoobiesBot v2.4"
BOTURL = "https://github.com/OverTheWireOrg/OverTheWire-boobiesbot"

try:
    import Image
    import aalib
    use_aalib = True
except ImportError:
    use_aalib = False
    print "aalib not found on this system..."

class BoobiesBot(GenericIRCBot):
    def __init__(self): #{{{
        self.catchall = self.handle_catchall
	self.commandData = {
	    "!help": { 
	    	"fn": self.handle_HELP, 
		"argc": 0, 
		"tillEnd": False,
		"help": "this help text",
		"msgtypes": ["private"],
	    },
	    "!boobies": { 
	    	"fn": self.handle_BOOBIES, 
		"argc": self.DontCheckARGC, 
		"tillEnd": True,
		"help": "get a random boobies link, or add one if argument is given. Hash-tags can be added behind the URL",
		"msgtypes": ["private", "public", "directed"],
	    },
            "!delboobies": {
                "fn": self.handle_DELBOOBIES,
                "argc": 1,
                "tillEnd": True,
                "help": "delete a boobies URL by ID",
		"msgtypes": ["public", "directed"],
            },
            "!aaboobies": {
                "fn": self.handle_AABOOBIES,
                "argc": 0,
                "tillEnd": False,
                "help": "get random AA boobies in query",
		"msgtypes": ["private"],
            },
            "!info": {
                "fn": self.handle_INFO,
                "argc": 0,
                "tillEnd": False,
                "help": "get info on this bot",
		"msgtypes": ["private", "public", "directed"],
            },
	    "!tag": { 
	    	"fn": self.handle_TAG, 
		"argc": self.DontCheckARGC, 
		"tillEnd": False,
		"help": "add tags to a given ID",
		"msgtypes": ["private", "public", "directed"],
	    },
	    "!deltag": { 
	    	"fn": self.handle_DELTAG, 
		"argc": self.DontCheckARGC, 
		"tillEnd": False,
		"help": "remove tags from a given ID",
		"msgtypes": ["public", "directed"],
	    },
	    "!listtags": { 
	    	"fn": self.handle_LISTTAGS, 
		"argc": self.DontCheckARGC, 
		"tillEnd": False,
		"help": "shows the hashtags in the system that match a given needle",
		"msgtypes": ["private", "public", "directed"],
	    },
	}
    #}}}

    def subhandle_RANDOM_BOOBIES(self, req): #{{{
	msgfmt = "[%s] %s (%s)"
	taglist = req["words"][1:]

	if any(not self.factory.db.isValidTag(x) for x in taglist):
	    self.sendReply(req, "Found no such boobies :(")
	    return

	# if we get here, then we have no idea what the user means... return a random URL
	(url, bid, tags) = self.factory.db.getRandomBoobies(taglist)
	if url:
	    tagmsg = ""
	    if tags and len(tags) > 0:
	        tagmsg = "Tags: %s" % ",".join(tags)
	    else:
	        tagmsg = "No tags"
	    self.sendReply(req, msgfmt % (bid, url, tagmsg))
	else:
	    self.sendReply(req, "Found no such boobies :(")
    #}}}
    def subhandle_SPECIFIC_BOOBIES(self, req, url, bid, tags): #{{{
	# we found a URL that matches an ID specified by the user, return it
	# ugh, duplicate code much?
	tagmsg = ""
	msgfmt = "[%s] %s (%s)"
	if tags and len(tags) > 0:
	    tagmsg = "Tags: %s" % ",".join(tags)
	else:
	    tagmsg = "No tags"
	self.sendReply(req, msgfmt % (bid, url, tagmsg))
    #}}}
    def subhandle_ADD_BOOBIES(self, req, url): #{{{
	if req["msgtype"] == "private":
	    self.sendReply(req, "Sorry, adding is not allowed in this message mode.")
	    return

	if self.factory.db.alreadyStored(url):
	    self.sendReply(req, "Thanks, but I already had those boobies <3")
	    return
	else:
	    bid = self.factory.db.addBoobies(url, addedby=req["fromuser"])
	    msg = "Thanks for the boobies (id=%s)! <3" % bid
	    if len(req["words"][1:]) > 1:
		(suc, errmsg) = self.factory.db.addTags(bid, req["words"][2:], addedby=req["fromuser"])
		if not suc:
		    msg += ", but I couldn't add the tags: %s :(" % errmsg
	    self.sendReply(req, msg)
	    return
    #}}}

    def handle_BOOBIES(self, req): #{{{
        if len(req["words"]) > 1:
	    # if the first argument is a URL, add it
	    if req["words"][1].startswith(("http://","https://")):
		self.subhandle_ADD_BOOBIES(req, req["words"][1])
		return

	    # if the first argument is a valid ID, display it
	    (url, bid, tags) = self.factory.db.getSpecificBoobies(req["words"][1])
	    if url:
		self.subhandle_SPECIFIC_BOOBIES(req, url, bid, tags)
		return
	    
        # otherwise, assume the message has hashtags and return a random record
	self.subhandle_RANDOM_BOOBIES(req)
#}}}
    def handle_DELBOOBIES(self, req): #{{{
        boobieid = req["words"][1]
	url,_,tags = self.factory.db.delBoobies(boobieid)
	if url:
	    tagmsg = ""
	    if tags and len(tags) > 0:
		tagmsg = "Tags: %s" % ",".join(tags)
	    else:
		tagmsg = "No tags"
	    self.sendReply(req, "removed boobies url %s -- %s (%s)" % (boobieid, url, tagmsg))
	else:
	    self.sendReply(req, "Could not remove those boobies (id %s)" % boobieid)

#}}}
    def handle_AABOOBIES(self, req): #{{{
    	if not use_aalib:
	    self.sendReply(req, "Sorry, this platform does not support aalib :(")
	else:
            width = 60
            height= 30
            (url, bid) = self.factory.db.getRandomBoobies()
            screen = aalib.AsciiScreen(width=width, height=height)
            fp = StringIO(urllib2.urlopen(url).read())
            image = Image.open(fp).convert('L').resize(screen.virtual_size)
            screen.put_image((0, 0), image)
	    output= screen.render()
	    out_arr = output.split()
	    for i in xrange(height):
		self.sendReply(req, out_arr[i])
#}}}
    def handle_INFO(self, req): #{{{
	self.sendReply(req, "I am %s and I hold %d URLs. Contribute to my sourcecode via pull-requests on %s." % (FULLNAME, self.factory.db.getRecordCount(), BOTURL))
	return
#}}}
    def handle_TAG(self, req): #{{{
	tags = req["words"][1:]
	if len(tags) > 1:
	    (suc, msg) = self.factory.db.addTags(tags[0], tags[1:], addedby=req["fromuser"])
	    if suc:
		self.sendReply(req, "Tags added <3")
	    else:
		self.sendReply(req, "Failed to add tags: %s :(" % msg)
	else:
	    self.sendReply(req, "Specify an ID followed by hashtags")
#}}}
    def handle_DELTAG(self, req): #{{{
	tags = req["words"][1:]
	if len(tags) > 1:
	    (suc, msg) = self.factory.db.delTags(tags[0], tags[1:])
	    if suc:
		self.sendReply(req, "Tags removed <3")
	    else:
		self.sendReply(req, "Failed to remove tags: %s :(" % msg)
	else:
	    self.sendReply(req, "Specify an ID followed by hashtags")
#}}}
    def handle_LISTTAGS(self, req): #{{{
	tags = req["words"][1:]
	matching = self.factory.db.getTagNames(tags[0] if len(tags) > 0 else None)

	if len(matching) > 0:
	    self.sendReply(req, "Known tags: %s" % ",".join(matching))
	else:
	    self.sendReply(req, "No known tags :(")

#}}}

    def looksLikeValidBoobiesURL(self, url): #{{{
        regex = [
	    r'^(http|https)://.*\.(png|jpg|jpeg|gif)'
	]

	isurl = any(re.match(x, url) for x in regex)
	return isurl
    #}}}
    def handle_catchall(self, req): #{{{
    	for url in req["words"]:
	    if self.looksLikeValidBoobiesURL(url) and not self.factory.db.alreadyStored(url):
		if isBoobiesPicture(url):
		    req["msg"] = "!boobies %s" % url
		    req["origmsg"] = "!boobies %s" % url
		    req["words"] = ["!boobies", url]
		    self.subhandle_ADD_BOOBIES(req, url)
    #}}}
    def joined(self, channel): #{{{
        pass
    #}}}

class BoobiesBotFactory(GenericIRCBotFactory):
    def __init__(self, proto, db, channel, nick): #{{{
        GenericIRCBotFactory.__init__(self, proto, channel, nick)
	self.db = db
# }}}


if __name__ == '__main__':
    # create factory protocol and application
    db = BoobiesDatabaseMongoDB(host=sys.argv[2] if len(sys.argv) > 2 else "localhost")
    f = BoobiesBotFactory(BoobiesBot, db, ["#social"], "BoobiesBot")

    # connect factory to this host and port
    reactor.connectTCP(sys.argv[1] if len(sys.argv) > 1 else "irc.overthewire.org", 6667, f)

    # run bot
    reactor.run()


