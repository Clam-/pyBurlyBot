#pyBurlyBot

# twisted imports
from twisted.words.protocols.irc import IRCClient, IRCBadModes, parseModes, X_DELIM, \
	symbolic_to_numeric, numeric_to_symbolic, ctcpExtract
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log

# system imports
from time import asctime, time
from collections import deque
#BurlyBot imports
from util.event import Event

# inject some other common symbolic IDs:
symbolic_to_numeric["RPL_YOURID"] = '042'
symbolic_to_numeric["RPL_LOCALUSERS"] = '265'
symbolic_to_numeric["RPL_GLOBALUSERS"] = '266'
# and the reverse:
numeric_to_symbolic["042"] = 'RPL_YOURID'
numeric_to_symbolic["265"] = 'RPL_LOCALUSERS'
numeric_to_symbolic["266"] = 'RPL_GLOBALUSERS'

class BurlyBot(IRCClient):
	"""BurlyBot"""
	
	erroneousNickFallback = "Burly"
	_names = {}
	linethrottle = 3
	_lines = 0
	_lastmsg = 0
	_lastCL = None
	# http://twistedmatrix.com/trac/browser/trunk/twisted/words/protocols/irc.py
	# irc_ and RPL_ methods are duplicated here verbatim so that we can dispatch higher level
	# events with the low level data intact.
	
	# custom sendline throttler. This might be overly complex and maybe the default IRCClient's
	# lineRate would be better
	def sendLine(self, line):
		t = time()
		if self._lastmsg + 1 < t:
			# if message hasn't been sent for 1 seconds, go for it
			self._lines += 1
			self._reallySendLine(line)
			# also reset the linecount if no msg for 2 seconds
			if self._lastmsg + 2 < t:
				self._lines = 1
		elif self._lines < self.linethrottle:
			# under threshold, go for it
			self._lines += 1
			self._reallySendLine(line)
		else:
			# cross threshold in 1 second, slow down
			self._dqueue.append(line)
			if not self._lastCL:
				self._lastCL = reactor.callLater(1.0, self._sendLine)
		self._lastmsg = t
		
	def _sendLine(self):
		t = time()
		if self._dqueue:
			line = self._dqueue.popleft()
			self._reallySendLine(line)
			self._lastmsg = t
			if self._dqueue:
				self._lastCL = reactor.callLater(1.0, self._sendLine)
			else:
				self._lastCL = None
		else:
			self._lastCL = None
		
		
	
	# TODO: IRC RFC says this is supposed to be able to support multiple channels... Make it so.
	#	Although if you passed a string with #channel,#channel2 it would work as intended but I think a list is more appropriate.
	# TODO: (also) Do this better.
	def names(self, channel):
		"""List the users in 'channel', usage: client.names('#testroom')"""
		self.sendLine('NAMES %s' % channel)

	### The following are "low level events" almost verbatim from IRCClient
	
	def irc_JOIN(self, prefix, params):
		"""
		Called when a user joins a channel.
		"""
		nick = prefix.split('!')[0]
		channel = params[-1]
		if nick == self.nickname:
			#self.state.joinchannel(channel)
			self.dispatch(self, Event("joined", prefix, params, hostmask=prefix, target=channel))
		else:
			#self.state.adduser(channel, nick)
			self.dispatch(self, Event("userJoined", prefix, params, hostmask=prefix, target=channel))

	def irc_PART(self, prefix, params):
		"""
		Called when a user leaves a channel.
		"""
		nick = prefix.split('!')[0]
		channel = params[0]
		if nick == self.nickname:
			#self.state.leavechannel(channel)
			self.dispatch(self, Event("left", prefix, params, hostmask=prefix, target=channel))
		else:
			#self.state.removeuser(channel, user)
			self.dispatch(self, Event("userLeft", prefix, params, hostmask=prefix, target=channel))
			

	def irc_QUIT(self, prefix, params):
		"""
		Called when a user has quit.
		"""
		#self.state.nukeuser(prefix.split('!')[0])
		self.dispatch(self, Event("userQuit", prefix, params, hostmask=prefix, msg=params[0]))

	# TODO: Store modes in state? (+m might be good to know about, as well as our own modes)
	def irc_MODE(self, prefix, params):
		"""
		Parse a server mode change message.
		"""
		channel, modes, args = params[0], params[1], params[2:]

		if modes[0] not in '-+':
			modes = '+' + modes

		if channel == self.nickname:
			# This is a mode change to our individual user, not a channel mode
			# that involves us.
			paramModes = self.getUserModeParams()
		else:
			paramModes = self.getChannelModeParams()

		try:
			added, removed = parseModes(modes, args, paramModes)
		except IRCBadModes:
			log.err(None, 'An error occured while parsing the following '
						  'MODE message: MODE %s' % (' '.join(params),))
		else:
			self.dispatch(self, Event("modeChanged", prefix, params, hostmask=prefix, target=channel,
				added=added, removed=removed, args=args))

	def irc_PRIVMSG(self, prefix, params):
		"""
		Called when we get a message.
		"""
		user = prefix
		channel = params[0]
		message = params[-1]

		if not message:
			# Don't raise an exception if we get blank message.
			return

		if message[0] == X_DELIM:
			m = ctcpExtract(message)
			if m['extended']:
				self.ctcpQuery(user, channel, m['extended'])

			if not m['normal']:
				return

			message = ' '.join(m['normal'])

		# privmsged because PRIVMSG is dispatched as the low-level version
		self.dispatch(self, Event("privmsged", prefix, params, hostmask=user, target=channel, msg=message))

	def irc_NOTICE(self, prefix, params):
		"""
		Called when a user gets a notice.
		"""
		user = prefix
		channel = params[0]
		message = params[-1]

		if message[0] == X_DELIM:
			m = ctcpExtract(message)
			if m['extended']:
				self.ctcpReply(user, channel, m['extended'])

			if not m['normal']:
				return

			message = ' '.join(m['normal'])

		self.dispatch(self, Event("noticed", prefix, params, hostmask=user, target=channel, msg=message))

	def irc_NICK(self, prefix, params):
		"""
		Called when a user changes their nickname.
		"""
		nick = prefix.split('!', 1)[0]
		if nick == self.nickname:
			self.nickChanged(params[0])
			self.dispatch(self, Event("nickChanged", prefix, params, hostmask=prefix, newname=params[0]))
		else:
			#update state user
			#self.state.changeuser(nick, params[0])
			self.dispatch(self, Event("userRenamed", prefix, params, hostmask=prefix, newname=params[0]))

	def irc_KICK(self, prefix, params):
		"""
		Called when a user is kicked from a channel.
		"""
		kicker = prefix.split('!')[0]
		channel = params[0]
		kicked = params[1]
		message = params[-1]
		if kicked.lower() == self.nickname.lower():
			#self.state.leavechannel(channel)
			self.dispatch(self, Event("kickedFrom", prefix, params, hostmask=prefix, target=channel, msg=message, kicked=kicked))
		else:
			#self.state.removeuser(kicked, user)
			self.dispatch(self, Event("userKicked", prefix, params, hostmask=prefix, target=channel, msg=message, kicked=kicked))

	def irc_TOPIC(self, prefix, params):
		"""
		Someone in the channel set the topic.
		"""
		#user = prefix.split('!')[0]
		channel = params[0]
		newtopic = params[1]
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, target=channel, newtopic=newtopic))

	# TODO: does irc_RPL_TOPIC get fired every time irc_TOPIC does?
	# Do we want to store topic in state?  Guess might as well, already have channel object (TODO)
	# Also, what is in params[0]?  ~SPOOKY~
	def irc_RPL_TOPIC(self, prefix, params):
		"""
		Called when the topic for a channel is initially reported or when it
		subsequently changes.
		"""
		#user = prefix.split('!')[0]
		channel = params[1]
		newtopic = params[2]
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, target=channel, newtopic=newtopic))

	def irc_RPL_NOTOPIC(self, prefix, params):
		"""
		...
		"""
		#user = prefix.split('!')[0]
		channel = params[1]
		newtopic = ""
		self.dispatch(self, Event("topicUpdated", prefix, params, hostmask=prefix, target=channel, newtopic=newtopic))

	def irc_RPL_ENDOFMOTD(self, prefix, params):
		"""
		Called when the bot receives RPL_ENDOFMOTD from the server.
		
		motd is a list containing the accumulated contents of the message of the day.
		"""
		motd = self.motd
		# The following sets self.motd to None, so we get the motd first
		IRCClient.irc_RPL_ENDOFMOTD(self, prefix, params)
		self.dispatch(self, Event("receivedMOTD", prefix, params, motd=motd))
			
	def irc_RPL_MYINFO(self, prefix, params):
		info = params[1].split(None, 3)
		while len(info) < 4:
			info.append(None)
		servername, version, umodes, cmodes = info
		self.dispatch(self, Event("myInfo", prefix, params, servername=servername, version=version, 
			umodes=umodes, cmodes=cmodes))
	
	# The following are custom, not taken from IRCClient:
	def irc_RPL_NAMREPLY(self, prefix, params):
		"""
		Called when NAMES reply is received from the server.
		"""
		print 'NAMES:', params
		channel = params[2]
		users = params[3].split(" ")
		self.dispatch(self, Event("nameReply", prefix, params, target=channel, users=users))

		for nick in users:
			nick = nick.lstrip(self.nickprefixes)
			if nick == self.nickname: continue
			#self.state.adduser(channel, nick)
	
	# TODO: this should probably collect the names from the above and dispatch them
	#  Not sure how to deal with multiple queries being returned at once, 
	#  maybe dict but don't want it to fill up with junk
	def irc_RPL_ENDOFNAMES(self, prefix, params):
		pass
	
	### Modified command handler from IRCCLient
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
		except:
			log.deferr()
		else:
			# All low level (RPL_type) events dispatched as they are
			self.dispatch(self, Event(command, prefix, params))
			if command in symbolic_to_numeric:
				# we are dispatching symbolic event so also dispatch the numeric event
				self.dispatch(self, Event(symbolic_to_numeric[command], prefix, params))
			if method is None:
				self.irc_unknown(prefix, command, params)
				
	
	### The following are "preprocessed" events normally called from IRCClient
	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		print "[Signed on]"
		
		#process nickprefixes
		prefixes = []
		for p, num in self.supported.getFeature("PREFIX").itervalues():
			#('~', 0)
			prefixes.append(p)
		self.nickprefixes = "".join(prefixes)
		
		for chan in self.settings.channels:
			self.join(*chan)
		
		# TODO: Issue #12 - smarter reconnect, resend
		self.container._setbotinst(self)
		self.state.resetnetwork()
		self.dispatch(self, Event("signedOn"))

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		IRCClient.joined(self, channel)
		print "[I have joined %s]" % channel
		#nuke channel
		# TODO: When implementing part/kick, use nukechannel(channel)
		#self.state.joinchannel(channel)
		# TODO: decide whether to use /names (auto) or /who... /names only gives nicknames, /who gives a crapton of infos...
		#self.names(channel)

	#TODO: proper CTCP things
	def action(self, hostmask, channel, msg):
		"""
		This will get called when the bot sees someone do an action.
		"""
		self.dispatch(self, Event(type="action", hostmask=hostmask, target=channel, msg=msg))
	
	#overriding msg
	# need to consider dipatching this event and allow for some override somehow
	# TODO: need to do some funky UTF-8 length calculation. Most naive one would be to keep adding a
	#	character so like for char in msg: t += char if len(t.encode("utf-8")) > max: send(old) else: old = t 
	#	or something... google or stackoverflow I guess WORRY ABOUT THIS LATER THOUGH
	def msg(self, user, msg, length=None):
		msg = msg.encode("utf-8")
		if length: IRCClient.msg(self, user, msg, length)
		else: IRCClient.msg(self, user, msg)
		
	# override the method that determines how a nickname is changed on
	# collisions. The default method appends an underscore.
	#Just kidding, actually let's do this after all - user option
	def alterCollidedNick(self, nickname):
		return nickname + self.settings.nicksuffix.encode("utf-8")
		
	def irc_unknown(self, prefix, command, params):
		if self.settings.debug:
			print "Unknown command: %s, %s, %s" % (prefix, command, params)
	
	
	### Custom outgoing methods
	# TODO: Need to add more of these for hooking other outbound events maybe, like notice...
	def sendmsg(self, channel, msg):
		#check if there's hooks, if there is, dispatch, if not, send directly
		if self.dispatcher.MSGHOOKS:
			#dest is Event.channel, or Event.args
			self.dispatch(self, Event(type="sendmsg", target=channel, msg=msg))
		else:
			self.msg(channel, msg)
	
	
	### Connection management methods
	def connectionMade(self):
		IRCClient.connectionMade(self)
		#reset connection factory delay:
		self.factory.resetDelay()

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		self.container._setbotinst(None)
		self.state.resetnetwork()
		print "[disconnected]"

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
		self.factor = 1.9021605823
	
	def buildProtocol(self, address):
		proto = ReconnectingClientFactory.buildProtocol(self, address)
		proto.container = self.container
		proto.state = self.container.state
		# for shortcut access:
		proto.settings = self.container._settings
		proto.dispatch = proto.settings.dispatcher.dispatch
		proto.dispatcher = proto.settings.dispatcher
		proto.nickname = proto.settings.nick.encode("utf-8")
		#throttle queue
		proto._dqueue = deque()
		return proto
		

