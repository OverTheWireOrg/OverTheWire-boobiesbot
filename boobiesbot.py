#!/usr/bin/python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import urllib2
from cStringIO import StringIO

# SQLite
import sqlite3

# system imports
import sys, os.path
from time import gmtime, strftime

from irc.GenericIRCBot import GenericIRCBot, GenericIRCBotFactory, log
from boobies.BoobiesClassifier import isBoobiesPicture
#from boobies.BoobiesDatabaseSQLite3 import *
from boobies.BoobiesDatabaseMongoDB import *

try:
    import Image
    import aalib
    use_aalib = True
except ImportError:
    use_aalib = False
    print "aalib not found on this system..."

class BoobiesBot(GenericIRCBot):
    def __init__(self): #{{{
	self.commandData = {
	    "!help": { 
	    	"fn": self.handle_HELP, 
		"argc": 0, 
		"tillEnd": False,
		"help": "this help text",
	    },
	    "!boobies": { 
	    	"fn": self.handle_BOOBIES, 
		"argc": self.DontCheckARGC, 
		"tillEnd": True,
		"help": "get a random boobies link, or add one if argument is given",
	    },
            "!delboobies": {
                "fn": self.handle_DEL,
                "argc": 1,
                "tillEnd": True,
                "help": "delete a boobies URL by ID",
            },
            "!aaboobies": {
                "fn": self.handle_AABOOBIES,
                "argc": 0,
                "tillEnd": False,
                "help": "get random AA boobies in query",
            },
            "!info": {
                "fn": self.handle_INFO,
                "argc": 0,
                "tillEnd": False,
                "help": "get info on this bot",
            },
	}

	self.commands = {
	    # only in direct user message, first word is the command
	    "private": ["!help", "!boobies", "!aaboobies", "!info"],
	    # only in channels, first word must be the command
	    "public": ["!boobies", "!delboobies", "!info"],
	    # only in channels, first word is the name of this bot followed by a colon, second word is the command
	    "directed": ["!boobies", "!delboobies", "!info"],
	}

	if not use_aalib:
	    del self.commandData["!aaboobies"]
	    self.commands = dict((k,[x for x in v if x != "!aaboobies"]) for (k,v) in self.commands.items())
    #}}}
    def handle_BOOBIES(self, msgtype, user, recip, cmd, url=""): #{{{
        if url and url.startswith(("http://","https://")):
	    if msgtype == "private":
		self.sendMessage(msgtype, user, recip, "Sorry, adding is not allowed in this message mode.")
		return

	    if self.factory.db.alreadyStored(url):
		self.sendMessage(msgtype, user, recip, "Thanks, but I already had those boobies <3")
		return
	    else:
		bid = self.factory.db.addBoobies(url)
		self.sendMessage(msgtype, user, recip, "Thanks for the boobies (id=%s)! <3" % bid)
		return

	msgfmt = "[%s] %s"
	if url:
	    (url, bid) = self.factory.db.getSpecificBoobies(url)
	    if url:
		self.sendMessage(msgtype, user, recip, msgfmt % (bid, url))
		return
	    else:
	    	# we fall back on a random selection, but let the user know he messed up anyway
		msgfmt += " (Not sure what you meant, but here you go)"
	
	(url, bid) = self.factory.db.getRandomBoobies()
	if url:
	    self.sendMessage(msgtype, user, recip, msgfmt % (bid, url))
	    return
	else:
	    self.sendMessage(msgtype, user, recip, "No boobies yet :(")
	    return
#}}}
    def handle_DEL(self, msgtype, user, recip, cmd, boobieid): #{{{
	if self.factory.db.delBoobies(boobieid):
	    self.sendMessage(msgtype, user, recip, "removed boobies url %s" % boobieid)
	else:
	    self.sendMessage(msgtype, user, recip, "Could not remove those boobies")

#}}}
    def handle_AABOOBIES(self, msgtype, user, recip, cmd): #{{{
    	if not use_aalib:
	    self.sendMessage(msgtype, user, recip, "Sorry, this platform does not support aalib :(")
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
		    self.sendMessage(msgtype ,user ,recip, out_arr[i])
#}}}
    def handle_INFO(self, msgtype, user, recip, cmd, url=""): #{{{
	self.sendMessage(msgtype, user, recip, "I am %s. Contribute to my sourcecode via pull-requests on %s." % (self.getFullname(), self.getURL()))
	return
#}}}

    def privmsg(self, user, channel, msg): #{{{
	# don't do anything if this message might be processed later on
	tokens = msg.lower().split(' ', 2)
	action = tokens[0];
	for cmd in self.commandData.keys():
	    if cmd in action:
		GenericIRCBot.privmsg(self, user, channel, msg)
		return
	
	# look at individual pieces, each may be an URL
    	maybeurls = msg.split()

	for url in maybeurls:
	    # URL must start with http:// or https://
            if not url.startswith(("http://","https://")):
	        continue
	    # URL must end with valid suffix
	    validSuffices = [".jpg", ".jpeg", ".gif", ".png"]
	    hasValidSuffix = False

	    for suf in validSuffices:
		if url.endswith(suf):
		    hasValidSuffix = True
		    break


	    if not hasValidSuffix:
	        continue

	    # Check if URL contains boobies, add it if it does
	    if isBoobiesPicture(url) and not self.factory.db.alreadyStored(url):
		GenericIRCBot.privmsg(self, user, channel, "!boobies %s" % url)
    #}}}
    def joined(self, channel): #{{{
        pass
    #}}}

class BoobiesBotFactory(GenericIRCBotFactory):
    def __init__(self, proto, db, channel, nick, fullname, url): #{{{
        GenericIRCBotFactory.__init__(self, proto, channel, nick, fullname, url)
	self.db = db
# }}}


if __name__ == '__main__':
    # create factory protocol and application
    #db = BoobiesDatabaseSQLite3()
    db = BoobiesDatabaseMongoDB()
    f = BoobiesBotFactory(BoobiesBot, db, ["#x"], "BoobiesBot2", "BoobiesBot v2.0", "https://github.com/StevenVanAcker/OverTheWire-boobiesbot")

    # connect factory to this host and port
    reactor.connectTCP(sys.argv[1] if len(sys.argv) > 1 else "irc.overthewire.org", 6667, f)

    # run bot
    reactor.run()


