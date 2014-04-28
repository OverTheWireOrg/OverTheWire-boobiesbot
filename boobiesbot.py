#!/usr/bin/python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import aalib
import Image
import urllib2
from cStringIO import StringIO

# SQLite
import sqlite3

# system imports
import sys, os.path
from time import gmtime, strftime

from GenericIRCBot import GenericIRCBot, GenericIRCBotFactory, log
from BoobiesClassifier import isBoobiesPicture

class BoobiesBot(GenericIRCBot):
    def __init__(self):
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

    def handle_BOOBIES(self, msgtype, user, recip, cmd, url=""): #{{{
        if url and url.startswith(("http://","https://")):
	    if msgtype == "private":
		self.sendMessage(msgtype, user, recip, "Sorry, adding is not allowed in this message mode.")
		return

	    if self.factory.db_alreadyStored(url):
		self.sendMessage(msgtype, user, recip, "Thanks, but I already had those boobies <3")
	    else:
		bid = self.factory.db_addBoobies(url)
		self.sendMessage(msgtype, user, recip, "Thanks for the boobies (id=%d)! <3" % bid)
	else:
	    (url, bid) = self.factory.db_getRandomBoobies()
	    if url:
	        self.sendMessage(msgtype, user, recip, "[%d] %s" % (bid, url))
	    else:
	        self.sendMessage(msgtype, user, recip, "No boobies yet :(")
#}}}
    def handle_DEL(self, msgtype, user, recip, cmd, boobieid): #{{{
        if not boobieid.isdigit():
            self.sendMessage(msgtype, user, recip, "The del command takes 1 numeric argument")
        else:
            boobieid = int(boobieid)
	    self.factory.db_delBoobies(boobieid)
	    self.sendMessage(msgtype, user, recip, "removed boobies url %d" % boobieid)

#}}}
    def handle_AABOOBIES(self, msgtype, user, recip, cmd): #{{{
            width = 60
            height= 30
            (url, bid) = self.factory.db_getRandomBoobies()
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
	for cmd in self.commandData.keys():
	    if cmd in msg:
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
	    if isBoobiesPicture(url) and not self.factory.db_alreadyStored(url):
		GenericIRCBot.privmsg(self, user, channel, "!boobies %s" % url)
    #}}}
    def joined(self, channel): #{{{
        pass
    #}}}

class BoobiesBotFactory(GenericIRCBotFactory):
    def __init__(self, proto, channel, nick, fullname, url): #{{{
        GenericIRCBotFactory.__init__(self, proto, channel, nick, fullname, url)
	# if the db file doesn't exist, create it
	self.db_init("boobies.db")
# }}}
    def db_init(self, fn): #{{{
	if os.path.exists(fn):
	    self.db = sqlite3.connect(fn)
	else:
	    self.db = sqlite3.connect(fn)
	    cu = self.db.cursor()
	    cu.execute("create table boobies (url varchar)")
	    self.db.commit()
    #}}}
    def db_addBoobies(self, url): #{{{
	cu = self.db.cursor()
	cu.execute("insert into boobies values(?)", (url,))
	self.db.commit()
        return cu.lastrowid
    #}}}
    def db_alreadyStored(self, url): #{{{
	cu = self.db.cursor()
	cu.execute("select rowid from boobies where url = ?", (url,))
	row = cu.fetchone()
	if row:
	    return True
	else:
	    return False
    #}}}
    def db_getRandomBoobies(self): #{{{
	cu = self.db.cursor()
	cu.execute("select url, rowid from boobies order by random() limit 1")
	row = cu.fetchone()
	if row:
	    return (str(row[0]), int(row[1]))
	else:
	    return ("", 0)
    #}}}
    def db_delBoobies(self, bid): #{{{
        cu = self.db.cursor()
        cu.execute("delete from boobies where rowid=%d" % bid)
        self.db.commit()
    #}}}    


if __name__ == '__main__':
    # create factory protocol and application
    f = BoobiesBotFactory(BoobiesBot, ["#social"], "BoobiesBot", "BoobiesBot v1.3", "https://github.com/StevenVanAcker/OverTheWire-boobiesbot")

    # connect factory to this host and port
    reactor.connectTCP("irc.overthewire.org", 6667, f)

    # run bot
    reactor.run()


