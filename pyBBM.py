#pyBBM

# twisted imports
from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log

# system imports
from time import asctime, time, localtime
from sys import stdout
from os.path import join
from optparse import OptionParser

#bbm imports
from util import Settings
from util.state import addnetwork
from util.container import Container
from util.db import DBQuery, dbcommit, setupDB
from util.dispatcher import Dispatcher
from util.timer import Timers
from util.event import Event

class BBMBot(IRCClient):
	"""BBM"""
	# http://twistedmatrix.com/documents/11.0.0/api/twisted.words.protocols.irc.IRCClient.html
	#nickname = None
	#lineRate = 1
	
	# TODO: IRC RFC says this is supposed to be able to support multiple channels... Make it so.
	#	Although if you passed a string with #channel,#channel2 lol it would work as intended but I think a list is more appropriate.
	# TODO: (also) Do this better.
	def names(self, channel):
		"""List the users in 'channel', usage: client.names('#testroom')"""
		self.sendLine('NAMES %s' % channel)
		
	def irc_RPL_NAMREPLY(self, *nargs):
		"""Receive NAMES reply from server"""
		print 'NAMES:', nargs
		channel = nargs[1][2]
		users = nargs[1][3].split(" ")

		for nick in users:
			nick = nick.lstrip(self.nickprefixes)
			if nick == self.nickname: continue
			self.state.adduser(channel, nick)
		
	def irc_RPL_ENDOFNAMES(self, *nargs):
		"""Called when NAMES output is complete"""
		pass #TODO: lol dispatch? 
	
	def connectionMade(self):
		IRCClient.connectionMade(self)
		#reset connection factory delay:
		self.factory.resetDelay()

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		self.state.nukenetwork(None)
		print "[disconnected at %s]" % asctime(localtime(time()))

	# callbacks for events
	
	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		print "[Signed on]"
		
		#process nickprefixes
		prefixes = []
		for p, num in self.supported.getFeature("PREFIX").values():
			#('~', 0)
			prefixes.append(p)
		self.nickprefixes = "".join(prefixes)
		
		for chan in self.settings.channels:
			self.join(*chan)
		
		# TODO: change nukenetwork to reactor.callLater() or something.
		# This really should be called after channels have been joined/rejoined so that any queues messages can be sent to channels
		self.state.nukenetwork(self)
		Dispatcher.dispatch(self, Event(type="signedOn"))

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		print "[I have joined %s]" % channel
		#nuke channel
		# TODO: When implementing part/kick, use nukechannel(channel)
		self.state.joinchannel(channel)
		# TODO: decide whether to use /names (auto) or /who... /names only gives nicknames, /who gives a crapton of infos...
		#self.names(channel)
		Dispatcher.dispatch(self, Event(type="joined", channel=channel))

	# TODO: dunno if you want to make this lower level irc_JOIN override to catch hostmask or not. Up to you.
	#		You should probably make all hooks that get given a "nick" into their hostname lower level equiv so you can setup
	#		proper event.hostmask stuff... Just remember to call the original method IRCClient.irc_JOIN(stuff) at the end (or start, whatev)
	def userJoined(self, user, channel):
		self.state.adduser(channel, user)
		# TODO: Dispatcher.dispatch(self, Event(type="userJoined", hostmask=hostmask, channel=channel, msg=msg))
	
	
	# MASSIVE TODO: Freaking Griffin, you need to add all the IRC events already to this craps, this one you probably need to change
	#	to the lower level hostname version
	def userLeft(self, user, channel):
		self.state.removeuser(channel, user)
		# TODO: Do this state for user kicked, too... lol do this GRIFFAN. This is your punishment for being lazyshit and L4D
		# TODO: lol Dispatcher GRIFFIIINNNNNNN
	
	def privmsg(self, hostmask, channel, msg):
		"""This will get called when the bot receives a message."""
		Dispatcher.dispatch(self, Event(type="privmsg", hostmask=hostmask, channel=channel, msg=msg))

	def action(self, hostmask, channel, msg):
		"""This will get called when the bot sees someone do an action."""
		Dispatcher.dispatch(self, Event(type="action", hostmask=hostmask, channel=channel, msg=msg))

	def irc_NICK(self, hostmask, params):
		"""
		Called when a user changes their nickname.
		"""
		nick = hostmask.split('!', 1)[0]
		if nick == self.nickname:
			self.nickChanged(params[0])
			Dispatcher.dispatch(self, Event(type="nickChanged", hostmask=hostmask, args={'newname': params[0]}))
		else:
			self.userRenamed(nick, params[0])
			#update state user
			self.state.changeuser(nick, params[0])
			Dispatcher.dispatch(self, Event(type="userRenamed", hostmask=hostmask, args={'newname': params[0]}))
		
	
	# TODO: Need to add more of these for hooking other outbound events maybe, like notice...
	def sendmsg(self, channel, msg):
		#check if there's hooks, if there is, dispatch, if not, send directly
		if Dispatcher.hostmap[self.settings.name]["MSGHOOKS"]:
			#dest is Event.channel, or Event.args
			Dispatcher.dispatch(self, Event(type="sendmsg", channel=channel, msg=msg))
		else:
			self.msg(channel, msg)
	
	#overriding msg
	# need to consider dipatching this event and allow for some override somehow
	# TODO: need to do some funky UTF-8 length calculation. Most naive one would be to keep adding a
	#	character so like for char in msg: t += char if len(t.encode("utf-8")) > max: send(old) else: old = t 
	#	or something... google or stackoverflow I guess WORRY ABOUT THIS LATER THOUGH
	def msg(self, user, msg, length=None):
		msg = msg.encode("utf-8")
		if length: IRCClient.msg(self, user, msg, length)
		else: IRCClient.msg(self, user, msg)
	
	#def myInfo(self, servername, version, umodes, cmodes):
		#We could always use this to get server hostname
		# more like dispatch
		
	# override the method that determines how a nickname is changed on
	# collisions. The default method appends an underscore.
	#Just kidding, actually let's do this after all - user option
	def alterCollidedNick(self, nickname):
		return nickname + self.settings.nicksuffix


class BBMBotFactory(ReconnectingClientFactory):
	"""A factory for BBMBot.
	A new protocol instance will be created each time we connect to the server.
	"""

	# the class of the protocol to build when new connection is made
	protocol = BBMBot

	def __init__(self, serversettings):
		#reconnect settings
		self.serversettings = serversettings
		self.maxDelay = 45
		self.factor = 1.6180339887498948
	
	def buildProtocol(self, address):
		proto = ReconnectingClientFactory.buildProtocol(self, address)
		proto.settings = self.serversettings
		proto.state = self.serversettings.state
		proto.nickname = self.serversettings.nick
		return proto



if __name__ == '__main__':
	from os.path import exists
	# initialize logging
	templog = log.startLogging(stdout)
	
	parser = OptionParser(usage="usage: %prog [options] [configfile]")
	parser.add_option("-d", "--dummy", action="store_true", dest="dummy", default=None,
		help="Dummy option. Placeholder.")
	(options, args) = parser.parse_args()
	#get settings file
	settingsf = None
	if len(args) > 0:
		settingsf = args[0]
	
	#make settings object with defaults.json
	#then make settings object with options.json and converge somehow...
	# I've done this before ghetto style, but we'll see what happens. 
	#(okay it's going to be pretty different to what I've done before)
	if settingsf and exists(settingsf):
		Settings.configfile = settingsf
	else:
		print "Settings file not found, running with defaults..."
	Settings.reload()
	#setup log options
	if not Settings.console:
		templog.stop()
		log.startLogging(open(join(Settings.cwd, "bbm.log"), 'a'), setStdout=False)
	# else:
		# log.startLogging(stdout)
	
	setupDB(join(Settings.cwd, Settings.datafolder))
	DBQuery.dbThread.start()
	try: Dispatcher.reload()
	except:
		DBQuery.dbQueue.put("STOP")
		raise
	
	#start dbcommittimer
	#def addtimer(cls, name, interval, f, kwargs={}, reps=None, startnow=False):
	Timers._addInternaltimer("_dbcommit", 60*60, dbcommit) #every hour (60*60)
	
	# create factory protocol and application
	#f = BBMBotFactory(sys.argv[1], sys.argv[2])
	for server in Settings.servers.values():
		#add wrapper to state
		addnetwork(server, Container(server, BBMBot))
		reactor.connectTCP(server.host, server.port, BBMBotFactory(server))
	
	# run bot
	reactor.run()
	#stop timers or just not care...
	Timers._stopall()
	DBQuery.dbQueue.put("STOP")
	DBQuery.dbThread.join()
