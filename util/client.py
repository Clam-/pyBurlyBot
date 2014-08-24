#pyBurlyBot

# twisted imports
from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log

# system imports
from time import asctime

#BurlyBot imports
from util.event import Event

class BurlyBot(IRCClient):
	"""BurlyBot"""
	# http://twistedmatrix.com/documents/11.0.0/api/twisted.words.protocols.irc.IRCClient.html
	#nickname = None
	#lineRate = 1
	
	# TODO: IRC RFC says this is supposed to be able to support multiple channels... Make it so.
	#	Although if you passed a string with #channel,#channel2 it would work as intended but I think a list is more appropriate.
	# TODO: (also) Do this better.
	def names(self, channel):
		"""List the users in 'channel', usage: client.names('#testroom')"""
		self.sendLine('NAMES %s' % channel)

	def irc_RPL_WELCOME(self, prefix, params):
		"""
		Called when we have received the welcome from the server.
		"""
		IRCClient.irc_RPL_WELCOME(self, prefix, params)
		self.dispatch(self, Event("signedOn", prefix, params, hostmask=prefix))

	def irc_JOIN(self, prefix, params):
		"""
		Called when a user joins a channel.
		"""
		IRCClient.irc_JOIN(self, prefix, params)
		nick = prefix.split('!')[0]
		channel = params[-1]
		if nick == self.nickname:
			#self.state.joinchannel(channel)
			self.dispatch(self, Event("joined", prefix, params, hostmask=prefix, channel=channel))
		else:
			#self.state.adduser(channel, nick)
			self.dispatch(self, Event("userJoined", prefix, params, hostmask=prefix, channel=channel))

	def irc_PART(self, prefix, params):
		"""
		Called when a user leaves a channel.
		"""
		IRCClient.irc_PART(self, prefix, params)
		nick = prefix.split('!')[0]
		channel = params[-1]
		if nick == self.nickname:
			#self.state.leavechannel(channel)
			self.dispatch(self, Event("left", prefix, params, hostmask=prefix, channel=channel))
		else:
			#self.state.removeuser(channel, user)
			self.dispatch(self, Event("userLeft", prefix, params, hostmask=prefix, channel=channel))

	def irc_QUIT(self, prefix, params):
		"""
		Called when a user has quit.
		"""
		IRCClient.irc_QUIT(self, prefix, params)
		#self.state.nukeuser(prefix.split('!')[0])
		self.dispatch(self, Event("userQuit", prefix, params, hostmask=prefix))

	# IRCClient does useful parsing for us here and doesn't omit anything
	# TODO: Store modes in state? (+m might be good to know about, as well as our own modes)
	# TODO: Get access to prefix / params?  Not sure how to go about it
	def modeChanged(self, user, channel, set, modes, args):
		"""
		Called when user's or channel's modes are changed.
		
		Set is true if modes were added, false if they were removed.
		"""
		self.dispatch(self, Event("modeChanged", "", "", hostmask=user, channel=channel,
			args={'set': set, 'modes': modes, 'args': args}))

	def irc_PRIVMSG(self, prefix, params):
		"""
		This will get called when the bot receives a message.
		"""
		user = prefix
		channel = params[0]
		message = params[-1]

		# privmsged because PRIVMSG is dispatched as the low-level version
		self.dispatch(self, Event("privmsged", prefix, params, hostmask=user, channel=channel, msg=message))

	def irc_NOTICE(self, prefix, params):
		"""
		Called when the bot has received a notice from a user directed to it or a channel.
		"""
		IRCClient.irc_NOTICE(self, prefix, params)
		user = prefix
		channel = params[0]
		message = params[-1]
		self.dispatch(self, Event("noticed", prefix, params, hostmask=user, channel=channel, msg=message))

	def irc_NICK(self, prefix, params):
		"""
		Called when a user changes their nickname.
		"""
		IRCClient.irc_NICK(self, prefix, params)
		nick = prefix.split('!', 1)[0]
		if nick == self.nickname:
			# IRCClient handles tracking our name
			self.dispatch(self, Event("nickChanged", prefix, params, hostmask=hostmask, args={'newname': params[0]}))
		else:
			#update state user
			#self.state.changeuser(nick, params[0])
			self.dispatch(self, Event("userRenamed", prefix, params, hostmask=hostmask, args={'newname': params[0]}))

	def irc_KICK(self, prefix, params):
		"""
		Called when a user is kicked from a channel.
		"""
		IRCClient.irc_NICK(self, prefix, params)
		kicker = prefix.split('!')[0]
		channel = params[0]
		kicked = params[1]
		message = params[-1]
		if string.lower(kicked) == string.lower(self.nickname):
			#self.state.leavechannel(channel)
			self.dispatch(self, Event("kickedFrom", prefix, params, hostmask=prefix, channel=channel, msg=message, args={'kicked': kicked}))
		else:
			#self.state.removeuser(kicked, user)
			self.dispatch(self, Event("userKicked", prefix, params, hostmask=prefix, channel=channel, msg=message, args={'kicked': kicked}))

	def irc_TOPIC(self, prefix, params):
		"""
		Someone in the channel set the topic.
		"""
		IRCClient.irc_TOPIC(self, prefix, params)
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, channel=params[0], args={'newtopic': params[1]}))

	# TODO: does irc_RPL_TOPIC get fired every time irc_TOPIC does?
	# Do we want to store topic in state?  Guess might as well, already have channel object (TODO)
	# Also, what is in params[0]?  ~SPOOKY~
	def irc_RPL_TOPIC(self, prefix, params):
		"""
		Called when the topic for a channel is initially reported or when it
		subsequently changes.
		"""
		IRCClient.irc_RPL_TOPIC(self, prefix, params)
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, channel=params[1], args={'newtopic': params[2]}))

	def irc_RPL_NOTOPIC(self, prefix, params):
		"""
		...
		"""
		IRCClient.irc_RPL_NOTOPIC(self, prefix, params)
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, channel=params[1], args={'newtopic': ''}))

	def irc_RPL_ENDOFMOTD(self, prefix, params):
		"""
		Called when the bot receives RPL_ENDOFMOTD from the server.
		
		motd is a list containing the accumulated contents of the message of the day.
		"""
		motd = self.motd
		# The following sets self.motd to None, so we get the motd first
		IRCClient.irc_RPL_ENDOFMOTD(self, prefix, params)
		self.dispatch(self, Event("receivedMOTD", prefix, params, args={'motd': motd}))

	def irc_RPL_NAMREPLY(self, prefix, params):
		"""
		Called when NAMES reply is received from the server.
		"""
		print 'NAMES:', params
		channel = params[2]
		users = params[3].split(" ")
		self.dispatch(self, Event("nameReply", prefix, params, channel=channel, args={'users': users}))

		for nick in users:
			nick = nick.lstrip(self.nickprefixes)
			if nick == self.nickname: continue
			#self.state.adduser(channel, nick)

	def handleCommand(self, command, prefix, params):
		"""
		Determine the function to call for the given command and call it with
		the given arguments.
		"""
		method_name = "irc_%s" % command
		method = getattr(self, method_name, None)
		try:
			if method is not None:
				method(prefix, params)
			else:
				self.irc_unknown(prefix, command, params)
		except:
			log.deferr()
		else:
			# All low level events dispatched as BaseEvents
			# Downside to this way of doing it is you have to have a separate name for the preprocessed version
			# of basic commands, like PRIVMSG
			self.dispatch(self, Event(command, prefix, params))

	def connectionMade(self):
		IRCClient.connectionMade(self)
		#reset connection factory delay:
		self.factory.resetDelay()

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		self.container._setbotinst(None)
		self.state.resetnetwork()
		print "[disconnected at %s]" % asctime()

	# callbacks for events
	
	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		IRCClient.signedOn(self)
		print "[Signed on]"
		
		#process nickprefixes
		prefixes = []
		for p, num in self.supported.getFeature("PREFIX").values():
			#('~', 0)
			prefixes.append(p)
		self.nickprefixes = "".join(prefixes)
		
		for chan in self.container._settings.channels:
			self.join(*chan)
		
		# TODO: Issue #12 - smarter reconnect, resend
		self.container._setbotinst(self)
		self.state.resetnetwork()

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		IRCClient.joined(self, channel)
		print "[I have joined %s]" % channel
		#nuke channel
		# TODO: When implementing part/kick, use nukechannel(channel)
		#self.state.joinchannel(channel)
		# TODO: decide whether to use /names (auto) or /who... /names only gives nicknames, /who gives a crapton of infos...
		#self.names(channel)

	def userJoined(self, user, channel):
		pass

	def userLeft(self, user, channel):
		pass

	def action(self, hostmask, channel, msg):
		"""
		This will get called when the bot sees someone do an action.
		"""
		self.dispatch(self, Event(type="action", hostmask=hostmask, channel=channel, msg=msg))

	# TODO: Need to add more of these for hooking other outbound events maybe, like notice...
	def sendmsg(self, channel, msg):
		#check if there's hooks, if there is, dispatch, if not, send directly
		if Dispatcher.hostmap[self.container.network]["MSGHOOKS"]:
			#dest is Event.channel, or Event.args
			self.dispatch(self, Event(type="sendmsg", channel=channel, msg=msg))
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
		return nickname + self.container._settings.nicksuffix.encode("utf-8")

class BurlyBotFactory(ReconnectingClientFactory):
	"""A factory for BurlyBot.
	A new protocol instance will be created each time we connect to the server.
	"""

	# the class of the protocol to build when new connection is made
	protocol = BurlyBot

	def __init__(self, serversettings):
		#reconnect settings
		self.container = serversettings.container
		self.maxDelay = 45
		self.factor = 1.6180339887498948
	
	def buildProtocol(self, address):
		proto = ReconnectingClientFactory.buildProtocol(self, address)
		proto.container = self.container
		proto.state = self.container.state
		proto.dispatch = self.container._settings.dispatcher.dispatch
		proto.nickname = self.container._settings.nick.encode("utf-8")
		return proto
		

