#preliminary State

# State class should only be used for reading by modules, and setting from main event triggers, I guess
# TODO: this means bads will happen when iterating over dictionaries because threads.
# TODO: make module accessors which are called in the reactor
# I think State is only marginally useful. I think it's overheads might be a waste.

# TODO: Make option to enable or disable state.

class Channel:
	def __init__(self, name, modes = None):
		self.name = name
		self.banlist = {} # [host] = (time, userwhosetban)
		self.users = {} # [nick] = User
		# TODO: Standify "modes". Is it a list? Of "@", "+", etc?
		#  in the case of channel modes, is it a list like ["+s", "+k pass"]?
		self.modes = {} # [nick] = modes, if nick == "" then channel modes
		self.topic = ""
		# (nick, ident, host, hostmask)
		self.topicsetby = (None, None, None, None)
		# TODO extra stuff to add... Some things might be network specific?

	def adduser(self, user, modes = None):
		if user.nick not in self.users:
			self.users[user.nick] = user
		user.channels.add(self.name)
			
	def changeuser(self, old, new):
		self.users[new] = self.users[old]
		del self.users[old]
		
	def removeuser(self, user):
		if user.nick in self.users:
			del self.users[user.nick]
	
	def settopic(self, topic, nick, ident, host, hostmask):
		self.topic = topic
		self.topicsetby(nick, ident, host, hostmask)

class User:
	def __init__(self, nick, ident=None, host=None, hostmask=None):
		self.channels = set()
		self.nick = nick
		self.ident = ident
		self.host = host
		self.hostmask = host
	
	# TODO: Should we really be caring enough to update hostmaks and stuff
	#	whenever we see the user do something?
	#	Should we actually be tracking the hostname and stuff? or just the nick?
	def refresh(self, ident, host, hostmask):
		if ident and self.ident != ident:
			self.ident = ident
		if host and self.host != host:
			self.host = host
		if hostmask and self.hostmask != hostmask:
			self.hostmask = hostmask
				

# TODO: function_renaming_cuz_conventions ~grifftask
class Network:
	def __init__(self, network):
		self.name = network
		self.users = {} # [nick] = User
		self.channels = {}
		self.motd = None
	
	def resetnetwork(self):
		#clear channels
		self.channels = {}
		self.users = {}
		
	def nukechannel(self, channel):
		if channel in self.channels:
			for user in self.channels[channel].users.itervalues():
				user.channels.remove(channel)
				if not user.channels:
					#user not known in any channels, remove existance
					del self.users[user.nick]
			del self.channels[channel]

	def userquit(self, nick):
		if nick in self.users:
			u = self.users[nick]
			for channel in u.channels:
				self.channels[channel].removeuser(u)
			del self.users[nick]

	def joinchannel(self, channel):
		self.nukechannel(channel)
		self.channels[channel] = Channel(channel)

	def leavechannel(self, channel):
		self.nukechannel(channel)

	def userjoin(self, channel, nick, ident=None, host=None, hostmask=None):
		u = None
		if nick not in self.users:
			u = User(nick, ident, host, hostmask)
			self.users[nick] = u
		else:
			u = self.users[nick]
			if ident or host or hostmask: u.refresh(ident, host, hostmask)
		self.channels[channel].adduser(u)

	def addban(self, channel, ban, stuff):
		# TODO: do this
		pass

	def userrename(self, oldnick, newnick):
		user = self.users[oldnick]
		del self.users[oldnick]
		self.users[newnick] = user
		#go through channels user is on
		for chan in user.channels:
			self.channels[chan].changeuser(oldnick, newnick)

	def userpart(self, channel, nick, ident=None, host=None, hostmask=None):
		if nick in self.users:
			u = self.users[nick]
			self.channels[channel].removeuser(u)
			if not u.channels:
				#user not known in any channels, remove existance
				del self.users[nick]
			else:
				if ident or host or hostmask: u.refresh(ident, host, hostmask)
		else:
			# TODO: remove this print, debug
			print "WARNING: user (%s) was never known about... 2SPOOKY" % user

	def modechange(self, channel, added, removed):
		c = self.channels[channel]
		for change in added:
			print "PROCESS THIS [ADDED] MODE: %s" % change
		for change in removed:
			print "PROCESS THIS [REMOVED] MODE: %s" % change

	def settopic(self, channel, newtopic, nick=None, ident=None, host=None, hostmask=None):
		self.channels[channel].settopic(newtopic, nick, ident, host, hostmask=None)
