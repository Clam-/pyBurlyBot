#pyBurlyBot

# twisted imports
from twisted.words.protocols.irc import IRCClient, IRCBadModes, parseModes, X_DELIM, \
	symbolic_to_numeric, numeric_to_symbolic, ctcpExtract, lowQuote
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python import log
from twisted.protocols.basic import LineReceiver

# system imports
from time import asctime, time
from collections import deque

#BurlyBot imports
from helpers import processHostmask, processListReply, PrefixMap, isIterable, commandlength, splitEncodedUnicode

# inject some other common symbolic IDs:
symbolic_to_numeric["RPL_YOURID"] = '042'
symbolic_to_numeric["RPL_LOCALUSERS"] = '265'
symbolic_to_numeric["RPL_GLOBALUSERS"] = '266'
symbolic_to_numeric["RPL_CREATIONTIME"] = '329'
symbolic_to_numeric["RPL_HOSTHIDDEN"] = '396'
symbolic_to_numeric["ERR_NOTEXTTOSEND"] = '412'
# and the reverse:
numeric_to_symbolic["042"] = 'RPL_YOURID'
numeric_to_symbolic["265"] = 'RPL_LOCALUSERS'
numeric_to_symbolic["266"] = 'RPL_GLOBALUSERS'
numeric_to_symbolic["329"] = 'RPL_CREATIONTIME'
numeric_to_symbolic["396"] = 'RPL_HOSTHIDDEN'
numeric_to_symbolic["412"] = 'ERR_NOTEXTTOSEND'

class BurlyBot(IRCClient):
	"""BurlyBot"""
	
	erroneousNickFallback = "Burly"
	linethrottle = 3
	_lines = 0
	_lastmsg = 0
	_lastCL = None
	supported = None
	altindex = 0
	prefixlen = None
	delimiter = '\r\n' # stick to specification
	
	# http://twistedmatrix.com/trac/browser/trunk/twisted/words/protocols/irc.py
	# irc_ and RPL_ methods are duplicated here verbatim so that we can dispatch higher level
	# events with the low level data intact.
	
	# custom sendline throttler. This might be overly complex but should behave similar to mIRC
	# where lines are only throttled once you cross a threshold. I don't know if the cooldown is similar though
	def sendLine(self, line):
		#main point of encoding outbound messages:
		if isinstance(line, unicode): line = line.encode(self.settings.encoding)
		if len(line) > 512: line = line[:512] #blindly truncate to not get killed for huge messages.
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

	# sticking to specification
	def _reallySendLine(self, line):
		return LineReceiver.sendLine(self, lowQuote(line) + '\r\n')
	def dataReceived(self, data):
		LineReceiver.dataReceived(self, data)
	
	def names(self, channels):
		"""List the users in a channel"""
		if isIterable(channels):
			self.sendLine('NAMES %s' % ",".join(channels))
		else:
			self.sendLine('NAMES %s' % channels)

	def banlist(self, channel):
		self.mode(channel, True, "b")
	
	###
	### The following are "low level events" almost (probably, maybe butchered) verbatim from IRCClient
	###
	def irc_JOIN(self, prefix, params):
		"""
		Called when a user joins a channel.
		"""
		nick, ident, host = processHostmask(prefix)
		channel = params[-1]
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
			if self.state: 
				self.state._joinchannel(channel)
				self.sendLine("MODE %s" % channel)
			self.dispatch(self, "joined", prefix=prefix, params=params, hostmask=prefix, target=channel, 
				nick=nick, ident=ident, host=host)
		else:
			if self.state: self.state._userjoin(channel, nick, ident, host, prefix)
			self.dispatch(self, "userJoined", prefix=prefix, params=params, hostmask=prefix, target=channel, 
				nick=nick, ident=ident, host=host)

	def irc_PART(self, prefix, params):
		"""
		Called when a user leaves a channel.
		"""
		nick, ident, host = processHostmask(prefix)
		channel = params[0]
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
			if self.state: self.state._leavechannel(channel)
			self.dispatch(self, "left", prefix=prefix, params=params, hostmask=prefix, target=channel, 
				nick=nick, ident=ident, host=host)
		else:
			if self.state: self.state._userpart(channel, nick, ident, host, prefix)
			self.dispatch(self, "userLeft", prefix=prefix, params=params, hostmask=prefix, target=channel, 
				nick=nick, ident=ident, host=host)
			

	def irc_QUIT(self, prefix, params):
		"""
		Called when a user has quit.
		"""
		nick, ident, host = processHostmask(prefix)
		if self.state: self.state._userquit(nick)
		self.dispatch(self, "userQuit", prefix=prefix, params=params, hostmask=prefix, msg=params[0], 
			nick=nick, ident=ident, host=host)

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
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
		else:
			paramModes = self.getChannelModeParams()

		try:
			added, removed = parseModes(modes, args, paramModes)
		except IRCBadModes:
			log.err(None, 'An error occured while parsing the following '
						  'MODE message: MODE %s' % (' '.join(params),))
		else:
			nick, ident, host = processHostmask(prefix)
			if self.state and (channel != self.nickname):
				self.state._modechange(channel, nick, added, removed)
			self.dispatch(self, "modeChanged", prefix=prefix, params=params, hostmask=prefix, target=channel,
				added=added, removed=removed, modes=modes, args=args, nick=nick, ident=ident, host=host)

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
				self.ctcpQuery(user, channel, m['extended'], params)

			if not m['normal']:
				return

			message = ' '.join(m['normal'])
		
		nick, ident, host = processHostmask(prefix)
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
		# These are actually messages, ctcp's aren't dispatched here
		self.dispatch(self, "privmsged", prefix=prefix, params=params, hostmask=user, target=channel, msg=message, 
			nick=nick, ident=ident, host=host)

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
				self.ctcpReply(user, channel, m['extended'], params)
			if not m['normal']:
				return
			message = ' '.join(m['normal'])
		
		nick, ident, host = processHostmask(prefix)
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
		self.dispatch(self, "noticed", prefix=prefix, params=params, hostmask=user, target=channel, msg=message,
			nick=nick, ident=ident, host=host)

	def irc_NICK(self, prefix, params):
		"""
		Called when a user changes their nickname.
		"""
		nick, ident, host = processHostmask(prefix)
		
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
			self.nickChanged(params[0])
			self.dispatch(self, "nickChanged", prefix=prefix, params=params, hostmask=prefix, newname=params[0])
		else:
			if self.state: self.state._userrename(nick, params[0], ident, host, prefix)
			self.dispatch(self, "userRenamed", prefix=prefix, params=params, hostmask=prefix, newname=params[0], 
				nick=nick, ident=ident, host=host)

	def irc_KICK(self, prefix, params):
		"""
		Called when a user is kicked from a channel.
		"""
		kicker = prefix.split('!')[0]
		channel = params[0]
		kicked = params[1]
		message = params[-1]
		if kicked.lower() == self.nickname.lower():
			if self.state: self.state._leavechannel(channel)
			self.dispatch(self, "kickedFrom", prefix=prefix, params=params, hostmask=prefix, target=channel, msg=message, kicked=kicked)
		else:
			if self.state: self.state._userpart(channel, kicked)
			self.dispatch(self, "userKicked", prefix=prefix, params=params, hostmask=prefix, target=channel, msg=message, kicked=kicked)

	def irc_RPL_TOPIC(self, prefix, params):
		"""
		Called when the topic for a channel is initially reported or when it
		subsequently changes.
		"""
		nick, ident, host = processHostmask(prefix)
		channel = params[1]
		newtopic = params[2]
		
		if self.state: self.state._settopic(channel, newtopic, nick, ident, host)
		self.dispatch(self, "topicUpdated", prefix=prefix, params=params, hostmask=prefix, target=channel, newtopic=newtopic, 
				nick=nick, ident=ident, host=host)

	def irc_RPL_NOTOPIC(self, prefix, params):
		"""
		...
		"""
		nick, ident, host = processHostmask(prefix)
		channel = params[1]
		newtopic = ""
		if self.state: self.state._settopic(channel, newtopic, nick, ident, host)
		self.dispatch(self, "topicUpdated", prefix=prefix, params=params, hostmask=prefix, target=channel, newtopic=newtopic, 
				nick=nick, ident=ident, host=host)

	def irc_RPL_ENDOFMOTD(self, prefix, params):
		"""
		Called when the bot receives RPL_ENDOFMOTD from the server.
		
		motd is a list containing the accumulated contents of the message of the day.
		"""
		motd = self.motd
		if self.state: self.state._motd = motd
		# The following sets self.motd to None, so we get the motd first
		IRCClient.irc_RPL_ENDOFMOTD(self, prefix, params)
		self.dispatch(self, "receivedMOTD", prefix=prefix, params=params, motd=motd)
			
	def irc_RPL_MYINFO(self, prefix, params):
		info = params[1].split(None, 3)
		while len(info) < 4:
			info.append(None)
		servername, version, umodes, cmodes = info
		self.dispatch(self, "myInfo", prefix=prefix, params=params, servername=servername, version=version, 
			umodes=umodes, cmodes=cmodes)
	
	### The following are custom, not taken from IRCClient:
	def irc_RPL_CHANNELMODEIS(self, prefix, params):
		"""
		Parse a RPL_CHANNELMODEIS message.
		"""
		channel, modes, args = params[1], params[2], params[3:]

		if modes[0] not in '-+':
			modes = '+' + modes
		try:
			added, _ = parseModes(modes, args, self.getChannelModeParams())
		except IRCBadModes:
			log.err(None, 'An error occured while parsing the following '
						  'MODE message: MODE %s' % (' '.join(params),))
		else:
			if self.state:
				self.state._modechange(channel, None, added, [])
			self.dispatch(self, "channelModeIs", prefix=prefix, params=params, hostmask=prefix, target=channel,
				added=added, modes=modes, args=args)
	
	def irc_RPL_CREATIONTIME(self, prefix, params):
		channel = params[1]
		t = params[2]
		self.dispatch(self, "creationTime", prefix=prefix, params=params, target=channel, creationtime=t)
	
	def irc_RPL_NAMREPLY(self, prefix, params):
		"""
		Called when NAMES reply is received from the server.
		"""
		channel = params[2]
		users = params[3].split()
		# TODO: should we give this event a copy of PrefixMap? check state._addusers as for why
		if self.state: self.state._addusers(channel, users)
		self._names.setdefault(channel, []).extend(users)
		self.dispatch(self, "nameReply", prefix=prefix, params=params, target=channel, users=users)
		
			
	def irc_RPL_ENDOFNAMES(self, prefix, params):
		channel = params[1]
		self.dispatch(self, "endOfNames", prefix=prefix, params=params, target=channel, users=self._names.pop(channel, []))
	
	def irc_RPL_BANLIST(self, prefix, params):
		"""
		Called when RPL_BANLIST reply is received from the server.
		"""
		channel, banmask, nick, ident, host, t, hostmask = processListReply(params)
		
		self._banlist.setdefault(channel, []).append((banmask, hostmask, t, nick))
		self.dispatch(self, "banList", prefix=prefix, params=params, target=channel, banmask=banmask, hostmask=hostmask, 
			timeofban=t, nick=nick, ident=ident, host=host)
	
	def irc_RPL_ENDOFBANLIST(self, prefix, params):
		channel = params[1]
		banlist = self._banlist.pop(channel, [])
		if self.state: self.state._addbans(channel, banlist)
		self.dispatch(self, "endOfBanList", prefix=prefix, params=params, target=channel, banlist=banlist)
			
	def irc_RPL_EXCEPTLIST(self, prefix, params):
		"""
		Called when RPL_EXCEPTLIST reply is received from the server.
		"""
		channel, exceptmask, nick, ident, host, t, hostmask = processListReply(params)

		self._exceptlist.setdefault(channel, []).append((exceptmask, hostmask, t, nick))
		self.dispatch(self, "exceptList", prefix=prefix, params=params, target=channel, exceptmask=exceptmask, hostmask=hostmask, 
			timeofban=t, nick=nick, ident=ident, host=host)
	
	def irc_RPL_ENDOFEXCEPTLIST(self, prefix, params):
		channel = params[1]

		exceptlist = self._exceptlist.pop(channel, [])
		if self.state: self.state._addexcepts(channel, exceptlist)
		self.dispatch(self, "endOfBanList", prefix=prefix, params=params, target=channel, exceptlist=exceptlist)

		
	def irc_RPL_INVITELIST(self, prefix, params):
		"""
		Called when RPL_INVITELIST reply is received from the server.
		"""
		channel, invitemask, nick, ident, host, t, hostmask = processListReply(params)

		self._invitelist.setdefault(channel, []).append((invitemask, hostmask, t, nick))
		self.dispatch(self, "inviteList", prefix=prefix, params=params, target=channel, invitemask=invitemask, hostmask=hostmask, 
			timeofban=t, nick=nick, ident=ident, host=host)
	
	def irc_RPL_ENDOFINVITELIST(self, prefix, params):
		channel = params[1]

		invitelist = self._invitelist.pop(channel, [])
		if self.state: self.state._addinvites(channel, invitelist)
		self.dispatch(self, "endOfInviteList", prefix=prefix, params=params, target=channel, invitelist=invitelist)
	
	def irc_RPL_ISUPPORT(self, prefix, params):
		IRCClient.irc_RPL_ISUPPORT(self, prefix, params)
		# This seems excessive but it's the only way to reliably update the prefixmap
		self.prefixmap.loadfromprefix(self.supported.getFeature("PREFIX").iteritems())
		
	# This method is interesting, for example ERROR gets sent from Rizon when you quit
	# TODO: find out what to actually do with this.
	def irc_ERROR(self, prefix, params):
		print "ERROR received: %s" % params
		
	###
	### Modified command handler from IRCCLient
	###
	def handleCommand(self, command, prefix, params):
		"""
		Determine the function to call for the given command and call it with
		the given arguments.
		"""
		method_name = "irc_%s" % command
		method = getattr(self, method_name, None)
		#print "INCOMING (%s): %s, %s" % (command, prefix, params)
		try:
			if method is not None:
				method(prefix, params)
		except:
			log.deferr()
		else:
			# All low level (RPL_type) events dispatched as they are
			self.dispatch(self, command, prefix=prefix, params=params)
			if command in symbolic_to_numeric:
				# we are dispatching symbolic event so also dispatch the numeric event
				self.dispatch(self, symbolic_to_numeric[command], prefix=prefix, params=params)
			if method is None:
				self.irc_unknown(prefix, command, params)

	def lineReceived(self, line):
		#print "---%s---" % line
		IRCClient.lineReceived(self, line)
				
	###
	### The following are "preprocessed" events normally called from IRCClient and mostly duplicated from IRCClient
	###
	def ctcpQuery(self, user, channel, messages, params):
		"""
		Dispatch method for any CTCP queries received.
		Duplicate tags ignored.
		Override from IRCClient
		"""
		seen = set()
		nick, ident, host = processHostmask(user)
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
		for tag, data in messages:
			if tag not in seen:
				#dispatch event
				self.dispatch(self, "ctcpQuery", prefix=user, params=params, hostmask=user, target=channel, tag=tag, 
					data=data, nick=nick, ident=ident, host=host)
			seen.add(tag)
			
	def ctcpReply(self, user, channel, messages, params):
		"""
		Dispatch method for any CTCP replies received.
		Duplicate tags ignored.
		Override from IRCClient
		"""
		seen = set()
		nick, ident, host = processHostmask(user)
		if nick == self.nickname:
			# take note of our prefix! (for message length calculation
			self.prefixlen = len(prefix)
		for tag, data in messages:
			if tag not in seen:
				#dispatch event
				self.dispatch(self, "ctcpReply", prefix=user, params=params, hostmask=user, target=channel, tag=tag, 
					data=data, nick=nick, ident=ident, host=host)
			seen.add(tag)
	
	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		print "[Signed on]"
		
		#process nickprefixes
		# reason for this is to class prefixes in to "op" and "voice"
		# and reason for that is because most important IRC operations are classed on OP or VOICE
		self.prefixmap = PrefixMap(self.supported.getFeature("PREFIX").iteritems())
		if self.state:
			self.state.prefixmap = self.prefixmap
		if self.settings.nickservpass:
			self.sendmsg("nickserv", "identify %s" % self.settings.nickservpass)
			# send notice to self to see if prefix changed, allow for some latency:
			reactor.callLater(1.0, self.notice, self.nickname, "\x1b")
		
		for chan in self.settings.channels:
			self.join(*chan)
		
		self.container._setBotinst(self)
		if self.state: self.state._resetnetwork()
		self.dispatch(self, "signedOn")

	# TODO: this currently doesn't get called. Do we want to dispatch these events? Or just make
	#	module catch ctcp events and check for ACTION tag?
	def action(self, hostmask, channel, msg, params):
		"""
		This will get called when the bot sees someone do an action.
		"""
		pass
	
	#overriding msg
	def msg(self, user, msg, length=None, strins=None):
		raise NotImplementedError("Use sendmsg instead.")
		
	# override the method that determines how a nickname is changed on
	# collisions.
	# TODO: At the moment this attempts to iterate the altnicks if it exists and falls back to
	# suffix after iterating. When to reset the iteration? At the moment it does it on connection
	# should probably make a reactor.callLater, and cancel it on disconnect or something.
	def alterCollidedNick(self, nickname):
		if self.settings.altnicks:
			if self.altindex < len(self.settings.altnicks):
				s = self.settings.altnicks[self.altindex]
				self.altindex += 1
				return s
			elif nickname != self.settings.nick:
				return self.settings.nick
		return (nickname + self.settings.nicksuffix)
		
	def irc_unknown(self, prefix, command, params):
		if self.settings.debug:
			print "Unknown command: %s, %s, %s" % (prefix, command, params)
	
	###
	### Custom outgoing methods
	###
	# TODO: Need to add more of these for hooking other outbound events maybe, like notice...
	def sendmsg(self, target, msg, strins=None, split=False, direct=False, fcfs=False):
		#check if there's hooks, if there is, dispatch, if not, send directly
		if self.dispatcher.MSGHOOKS and not direct:
			self.dispatch(self, "sendmsg", target=target, msg=msg, strins=None, fcfs=fcfs)
		else:
			self.sendLine(self._buildmsg(target, msg, split, strins, fcfs))
	
	# will return true if sendmsg can proceed without truncation, false otherwise.
	# will provide incorrect results if any sendmsg hooks change lengths of messages
	# TODO: (very low priority I guess) somehow get a builtmsg from sendmsg hooks
	# NOTE: USAGE OF THIS MESSAGE MUST TEST FOR TRUE AND FALSE EXPLICITLY. None will be returned if bot isn't connected
	#		at the time of call.
	def checkSendMsg(self, target, msg):
		return len(self._buildmsg(target, msg).encode(self.settings.encoding)) <= self.calcAvailableMsgLength("")
		
	def _buildmsg(self, target, message, split=False, strins=None, fcfs=False):
		if strins:
			message = self.assembleMsgWLen('PRIVMSG %s :%s' % (target, message), strins, fcfs)
			return message
		else:
			fmt = 'PRIVMSG %s :%%s' % (target,)
			if split:
				return (fmt % msg for msg in 
					splitEncodedUnicode(message, self.calcAvailableMsgLength(fmt % ""), encoding=self.settings.encoding, n=4))
			else:
				# blindly truncate message at sendLine level, also useful for checkSendMsg
				return fmt % message
	
	# helper method to automatically truncate string to be replaced
	# TODO: need decide on string format method, either "%s" % x or "{0}".format(x)
	def assembleMsgWLen(self, s, strins, fcfs):
		if isinstance(strins, basestring):
			return s % splitEncodedUnicode(strins, self.calcAvailableMsgLength(s)-2, encoding=self.settings.encoding)[0]
		if fcfs:
			if isIterable(strins):
				l = len(strins)-1
				for i, rep in enumerate(strins):
					# TODO: this is a little ghetto but I'm unsure of a better way at this point in time
					s = s % ((splitEncodedUnicode(rep, self.calcAvailableMsgLength(s)-(l-i), encoding=self.settings.encoding)[0],) + ("%s",)*(l-i))
				return s
			elif isinstance(strins, dict):
				# TODO: defaultdict makes this surprisingly straightforward. Maybe should make a custom list object that
				# returns "%s" for invalid indexes
				d = defaultdict(lambda: "%s")
				db = defaultdict(lambda: "")
				for key, value in strins.iteritems():
					d[key] = splitEncodedUnicode(value, self.calcAvailableMsgLength(s % db), encoding=self.settings.encoding)[0]
					s = s % d
				return s
			else:
				raise ValueError("Require list/tuple, dict, or string for strins.")
		else:
			# round 2, even divide
			l = len(strins)
			if isIterable(strins):
				segmentlength = int(floor((self.calcAvailableMsgLength(s)-(l*2)) / l))
				if isinstance(strins, tuple):
					strins = list(strins)
				for i, sr in enumerate(strins):
					strins[i] = splitEncodedUnicode(sr, segmentlength, encoding=self.settings.encoding)[0]
				return s % strins
				
			elif isinstance(strins, dict):
				db = defaultdict(lambda: "")
				segmentlength = int(floor((self.calcAvailableMsgLength(s % db) / l)))
				for key, value in strins.iteritems():
					strins[key] = splitEncodedUnicode(value, segmentlength, encoding=self.settings.encoding)[0]
				return s % strins
			else:
				raise ValueError("Require list/tuple, dict, or string for strins.")
	
	def calcAvailableMsgLength(self, command):
		if self.prefixlen:
			return 510 - self.prefixlen - len(command) # 510 = line terminator
		else:
			return self._safeMaximumLineLength(command) - 2 #line terminator

	###
	### Connection management methods
	###
	def connectionMade(self):
		IRCClient.connectionMade(self)
		self._names = {}
		self._banlist = {}
		self._exceptlist = {}
		self._invitelist = {}
		# TODO: I think this should be on "signedOn()" just in case part of the signon is causing instant disconnect
		# reset connection factory delay:
		self.factory.resetDelay()

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		self.container._setBotinst(None)
		if self.state: self.state._resetnetwork()
		# TODO: reason needs to be properly formatted/actual reason being extracted from the "Failure" or whatever
		print "[disconnected: %s]" % reason

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
		# for shortcut access:
		proto.settings = self.container._settings
		if proto.settings.enablestate: proto.state = self.container.state
		else: proto.state = None
		proto.dispatch = proto.settings.dispatcher.dispatch
		proto.dispatcher = proto.settings.dispatcher
		proto.nickname = proto.settings.nick
		#throttle queue
		proto._dqueue = deque()
		return proto
