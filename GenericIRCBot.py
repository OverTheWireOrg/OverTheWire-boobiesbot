#!/usr/bin/python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

# system imports
from time import gmtime, strftime
from random import randint

def log(m, c=""):
    pass
    #with open("vulnbot.log", "a") as f:
    #	mc = "# logged at " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " + c
    #	f.write(mc + "\n")
    #	f.write(m + "\n")
    #print(mc)
    #print(m)

class GenericIRCBot(irc.IRCClient):
    DontCheckARGC = -1
    commandData = {}
    commands = {
        "private": [],
        "public": [],
        "directed": [],
    }

    def getCommandRecords(self, msgtype):
        out = {}
	for c in self.commands[msgtype]:
	    out[c] = self.commandData[c]
	return out

    def getNickname(self):
        return self.factory.nickname

    def getFullname(self):
        return self.factory.fullname

    def getURL(self):
        return self.factory.url

    def getBaseNickname(self):
        return self.factory.basenickname

    def setNickname(self, nick):
        self.factory.nickname = nick
	self.nickname = nick

    def getReplyTarget(self, msgtype, user, channel):
        return {
	    "public": channel,
	    "directed": channel,
	    "private": user
	}[msgtype]

    def sendMessage(self, msgtype, user, channel, msg):
        prefix = user+": " if msgtype == "directed" else ""
	self.sendLine("PRIVMSG %s :%s%s" % (self.getReplyTarget(msgtype, user, channel), prefix, msg))

    def connectionMade(self): #{{{
    	self.setNickname(self.getNickname())
        irc.IRCClient.connectionMade(self)
#}}}
    def signedOn(self): #{{{
        """Called when bot has succesfully signed on to server."""
	[self.join(x) for x in self.factory.channels]
#}}}
    def alterCollidedNick(self, nickname): #{{{
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
	self.setNickname("%s-%03d" % (self.getBaseNickname(), randint(0, 1000)))
        return self.getNickname()
#}}}
    def privmsg(self, user, channel, msg): #{{{
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
	origmsg = msg
	error = ""

	# determine the type of command, select the correct set of handlers
	# and, in case of a directed message, strip of this bot's nickname
        if channel == self.getNickname(): 
	    # private message
	    msgtype = "private"
	else:
	    # check if directed at this nickname
	    key = self.getNickname() + ":"
	    keylen = len(key)
	    if msg.startswith(key):
	        msgtype = "directed"
	        msg = msg[keylen:]
	    else:
	        msgtype = "public"
	recset = self.getCommandRecords(msgtype)
	    	
	# split into words, words[0] contains the command if it exists
	words = msg.split()

	if len(words):
	    cmd = words[0]
	    if cmd in recset:
		rec = recset[cmd]
		c = rec["argc"]
	        if c == self.DontCheckARGC:
		    words = msg.split(None)
		else:
		    if len(words) >= (c+1):
			words = msg.split(None, c if rec["tillEnd"] else c+1)[:(c+1)]
		    else:
			error = "Not enough parameters: expecting %d, received %d" % (c, len(words) - 1)
	    else:
	        if msgtype == "public":
		    return
		error = "Unknown command %s" % (cmd)
	else:
	    if msgtype == "public":
		return
	    error = "What is it? Use !help if you're confused..."

	if error:
	    self.sendMessage(msgtype, user, channel, error)
	    print "Error msgtype=%s: [%s]" % (msgtype, error)
	    return
	    
	rec["fn"](msgtype, user, channel, *(words))
	log(origmsg, "User: %s, Recip: %s, Target: %s" % (user, channel, self.getReplyTarget(msgtype, user, channel)));
#}}}

    def handle_HELP(self, msgtype, user, recip, cmd): #{{{
	self.sendMessage(msgtype, user, recip, "I am %s from %s. Available commands (m=message, c=channel, d=directed):" % (self.getFullname(), self.getURL()))
	cmds = self.commandData.keys()
	cmds.sort()
	for k in cmds:
	    prefix = "["
	    prefix += "m" if k in self.commands["private"] else "-"
	    prefix += "c" if k in self.commands["public"] else "-"
	    prefix += "d" if k in self.commands["directed"] else "-"
	    prefix += "]"

	    helptext = self.commandData[k]["help"]
	    c = self.commandData[k]["argc"]
	    if c == self.DontCheckARGC:
	        args = "..."
	    else:
	    	args = " ".join(["<%s>" % chr(x+ord('a')) for x in range(0,c)])
	    self.sendMessage(msgtype, user, recip, "  %s %10s %-10s : %s" % (prefix, k,args, helptext))
#}}}


class GenericIRCBotFactory(protocol.ClientFactory):
    def __init__(self, proto, channels, nick, fullname, url): #{{{
        self.protocol = proto
        self.channels = channels
        self.nickname = nick
        self.basenickname = nick
        self.fullname = fullname
        self.url = url
# }}}
    def clientConnectionLost(self, connector, reason): #{{{
        """If we get disconnected, reconnect to server."""
        connector.connect()
#}}}
    def clientConnectionFailed(self, connector, reason): #{{{
        print "connection failed:", reason
        reactor.stop()
#}}}
