#!/usr/bin/python

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

# system imports
from time import gmtime, strftime
from random import randint

"""
This class should take care of the IRC connection.
We want the IRC bot to connect, join some channels
and remember what his nickname is and what channels he is on

any subclass can define commands to be executed
or can listen for certain regex?

Should there be a different structure to the bot?
Instead of...

Should commands be split up into records, instead of passing each value separately?

"""

def log(m, c=""):
    pass

class GenericIRCBot(irc.IRCClient):
    DontCheckARGC = -1
    commandData = {}
    commands = {
        "private": [],
        "public": [],
        "directed": [],
    }

    def getCommandRecord(self, cmd): #{{{
	if cmd in self.commandData:
	    return self.commandData[cmd]
	return None
#}}}
    def getNickname(self): #{{{
        return self.factory.nickname

#}}}
    def getBaseNickname(self): #{{{
        return self.factory.basenickname

#}}}
    def setNickname(self, nick): #{{{
        self.factory.nickname = nick
	self.nickname = nick

#}}}
    def getReplyTarget(self, msgtype, user, channel): #{{{
        return {
	    "public": channel,
	    "directed": channel,
	    "private": user
	}[msgtype]

#}}}
    def sendReply(self, req, msg): #{{{
        prefix = req["fromuser"]+": " if req["msgtype"] == "directed" else ""
	msg = msg.encode("ascii", "replace")
	self.sendLine("PRIVMSG %s :%s%s" % (self.getReplyTarget(req["msgtype"], req["fromuser"], req["to"]), prefix, msg))
#}}}
    def sendMessage(self, msgtype, user, channel, msg): #{{{
        prefix = user+": " if msgtype == "directed" else ""
	msg = msg.encode("ascii", "replace")
	self.sendLine("PRIVMSG %s :%s%s" % (self.getReplyTarget(msgtype, user, channel), prefix, msg))
#}}}
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

    def makeIRCrequest(self, src, dest, msg): #{{{
        req = {
	    "from": src,
	    "to": dest,
	    "origmsg": msg,
	    "msg": msg,
	    "fromuser": src.split('!', 1)[0],
	}


	# determine the type of command, select the correct set of handlers
	# and, in case of a directed message, strip of this bot's nickname
        if dest == self.getNickname(): 
	    # private message
	    req["msgtype"] = "private"
	else:
	    # check if directed at this nickname
	    key = self.getNickname() + ":"
	    keylen = len(key)
	    if msg.startswith(key):
	        req["msgtype"] = "directed"
	        req["msg"] = msg[keylen:]
	    else:
	        req["msgtype"] = "public"

	req["words"] = msg.split()
	req["cmd"] = req["words"][0] if len(req["words"]) > 0 else None

	return req
    #}}}
    def privmsg(self, user, channel, msg): #{{{ FIXME
        req = self.makeIRCrequest(user, channel, msg)

	if req["cmd"] != None:
	    # check the records...
	    cmdrec = self.getCommandRecord(req["cmd"])
	    print cmdrec

	    # if the command exists, but is not allowed in this message type, announce it
	    if not cmdrec:
	    	if req["msgtype"] != "public":
		    self.sendReply(req, "Unknown command %s" % req["cmd"])
		return

	    if req["msgtype"] not in cmdrec["msgtypes"]:
		self.sendReply(req, "This command should be used in another message mode")
		return

	    # otherwise, prepare the req to be passed to the user functions
	    c = cmdrec["argc"]
	    if c != self.DontCheckARGC:
		if len(req["words"]) >= (c+1):
		    req["words"] = req["msg"].split(None, c if cmdrec["tillEnd"] else c+1)[:(c+1)]
		else:
		    self.sendReply(req, "Not enough parameters: expecting %d, received %d" % (c, len(req["words"]) - 1))
		    return
	else:
	    if msgtype != "public":
		self.sendReply(req, "What is it? Use !help if you're confused...")
	    return

	    
	cmdrec["fn"](req)
#}}}

    def handle_HELP(self, req): #{{{
	self.sendReply(req, "Available commands (m=message, c=channel, d=directed):")
	cmds = self.commandData.keys()
	cmds.sort()
	for k in cmds:
	    prefix = "[%s]" % "".join([
	    "m" if "private" in self.commandData[k]["msgtypes"] else "-",
	    "c" if "public" in self.commandData[k]["msgtypes"] else "-",
	    "d" if "directed" in self.commandData[k]["msgtypes"] else "-"
	    ])

	    helptext = self.commandData[k]["help"]
	    c = self.commandData[k]["argc"]
	    if c == self.DontCheckARGC:
	        args = "..."
	    else:
	    	args = " ".join(["<%s>" % chr(x+ord('a')) for x in range(0,c)])
	    self.sendReply(req,"  %s %10s %-10s : %s" % (prefix, k,args, helptext))
#}}}


class GenericIRCBotFactory(protocol.ClientFactory):
    def __init__(self, proto, channels, nick): #{{{
        self.protocol = proto
        self.channels = channels
        self.nickname = nick
        self.basenickname = nick
# }}}
    def clientConnectionLost(self, connector, reason): #{{{
        """If we get disconnected, reconnect to server."""
        connector.connect()
#}}}
    def clientConnectionFailed(self, connector, reason): #{{{
        print "connection failed:", reason
        reactor.stop()
#}}}
