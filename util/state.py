#preliminary State

# State class should only be used for reading by modules, and setting from main event triggers, I guess
# I think State is only marginally useful. I think it's overheads might be a waste.

from time import time
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

class Channel:
	def __init__(self, name, modes = None):
		self.name = name
		self._users = {} # [nick] = User
		self._ops = set() # set of nicks
		self._voices = set() # set of nicks
		
		self.moderated = False
		self.inviteonly = False
		self.secret = False
		self.key = None
		self.private = False
		self.limit = None
		self.optopic = False
		self.noextmsg = False
		
		# NOTE: this will only be populated with what the bot sees
		# If you want this to be fully populated MODE #channel <b,e,I> will need to be issued
		# Also NOTE: exceptlist is a list of ban exceptions, invitelist is a list of users
		#	exempted from invite only.
		self._banlist = {} # [host] = nickwhosetban, time
		self._exceptlist = {} # [host] = nickwhosetexcept, time
		self._invitelist = {} # [host] = nickwhosetinvite, time
		
		self.topic = ""
		# (nick, ident, host, hostmask)
		self.topicsetby = (None, None, None, None)
		
	def _resetModeIs(self):
		self.moderated = False
		self.inviteonly = False
		self.secret = False
		self.key = None
		self.private = False
		self.limit = None
		self.optopic = False
		self.noextmsg = False

	# NOTE: access to these attributes may cause the bot to slow if in massive channels
	@property
	def users(self):
		return blockingCallFromThread(reactor, self._users.copy)
	@property
	def ops(self):
		return blockingCallFromThread(reactor, self._ops.copy)
	@property
	def voices(self):
		return blockingCallFromThread(reactor, self._voices.copy)
	@property
	def banlist(self):
		return blockingCallFromThread(reactor, self._banlist.copy)
	@property
	def exceptlist(self):
		return blockingCallFromThread(reactor, self._exceptlist.copy)
	@property
	def invitelist(self):
		return blockingCallFromThread(reactor, self._invitelist.copy)

	def _adduser(self, user, modes = None):
		if user.nick not in self._users:
			self._users[user.nick] = user
		user._channels.add(self.name)
			
	def _changeuser(self, old, new):
		self._users[new] = self._users[old]
		del self._users[old]
		
	def _removeuser(self, nick):
		if nick in self._users:
			del self._users[nick]
	
	def _settopic(self, topic, nick, ident, host, hostmask):
		self.topic = topic
		self._topicsetby = (nick, ident, host, hostmask)

class User:
	def __init__(self, nick, ident=None, host=None, hostmask=None):
		self._channels = set()
		self.nick = nick
		self.ident = ident
		self.host = host
		self.hostmask = host
	
	@property
	def channels(self):
		return blockingCallFromThread(reactor, self._channels.copy)
		
	# TODO: Should we really be caring enough to update hostmaks and stuff
	#	whenever we see the user do something?
	#	Should we actually be tracking the hostname and stuff? or just the nick?
	def _refresh(self, ident, host, hostmask):
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
		self._users = {} # [nick] = User
		self._channels = {}
		self.motd = None
	
	@property
	def users(self):
		return blockingCallFromThread(reactor, self._users.copy)
	@property
	def channels(self):
		return blockingCallFromThread(reactor, self._channels.copy)
	
	def _resetnetwork(self):
		#clear channels
		self._channels = {}
		self._users = {}
		
	def _nukechannel(self, channel):
		if channel in self._channels:
			for user in self._channels[channel]._users.itervalues():
				user._channels.remove(channel)
				if not user._channels:
					#user not known in any channels, remove existance
					del self._users[user.nick]
			del self._channels[channel]

	def _userquit(self, nick):
		if nick in self._users:
			u = self._users[nick]
			for channel in u._channels:
				self._channels[channel]._removeuser(u.nick)
			del self._users[nick]

	def _joinchannel(self, channel):
		self._nukechannel(channel)
		self._channels[channel] = Channel(channel)

	def _leavechannel(self, channel):
		self._nukechannel(channel)

	def _userjoin(self, channel, nick, ident=None, host=None, hostmask=None):
		u = None
		if nick not in self._users:
			u = User(nick, ident, host, hostmask)
			self._users[nick] = u
		else:
			u = self._users[nick]
			if ident or host or hostmask: u._refresh(ident, host, hostmask)
		self._channels[channel]._adduser(u)

	@staticmethod
	def _processlist(l):
		d = {}
		for (mask, _, t, nick) in l:
			d[mask] = (nick, int(t))
		return d
	
	def _addinvites(self, channel, invitelist):
		self._channels[channel]._invitelist = self._processlist(invitelist)
	
	def _addexcepts(self, channel, exceptlist):
		self._channels[channel]._exceptlist = self._processlist(exceptlist)
		
	def _addbans(self, channel, banlist):
		self._channels[channel]._banlist = self._processlist(banlist)

	def _userrename(self, oldnick, newnick):
		user = self._users[oldnick]
		del self._users[oldnick]
		self._users[newnick] = user
		#go through channels user is on
		for chan in user._channels:
			self._channels[chan]._changeuser(oldnick, newnick)

	def _userpart(self, channel, nick, ident=None, host=None, hostmask=None):
		if nick in self._users:
			u = self._users[nick]
			self._channels[channel]._removeuser(u.nick)
			if not u._channels:
				#user not known in any channels, remove existance
				del self._users[nick]
			else:
				if ident or host or hostmask: u._refresh(ident, host, hostmask)
		else:
			# TODO: remove this print, debug
			print "WARNING: user (%s) was never known about... 2SPOOKY" % user

	# TODO: This could probably be less wordly, also check if KeyErrors and pop's
	#	will present a problem
	def _modechange(self, channel, nick, added, removed, reset=True):
		c = self._channels[channel]
		if reset: c._resetModeIs()
		for mode, arg in added:
			if mode in self.prefixmap.opcmds:
				c._ops.add(arg)
			elif mode == "b":
				c._banlist[arg] = (nick, int(time()))
			elif mode == "e":
				c._exceptlist[arg] = (nick, int(time()))
			elif mode == "i":
				c.inviteonly = True
			elif mode == "m":
				c.moderated = True
			elif mode == "n":
				c.noextmsg = True
			elif mode == "p":
				c.private = True
			elif mode == "s":
				c.secret = True
			elif mode == "t":
				c.optopic = True
			elif mode == "k":
				c.key = arg
			elif mode == "l":
				c.limit = arg
			elif mode == "I":
				c._invitelist[arg] = (nick, int(time()))
			elif mode in self.prefixmap.voicecmds:
				c._voices.add(arg)
				
		for change in removed:
			if mode in self.prefixmap.opcmds:
				try: c._ops.remove(arg)
				except KeyError: pass
			elif mode == "b":
				c._banlist.pop(arg, None)
			elif mode == "e":
				c._exceptlist.pop(arg, None)
			elif mode == "i":
				c.inviteonly = False
			elif mode == "m":
				c.moderated = False
			elif mode == "n":
				c.noextmsg = False
			elif mode == "p":
				c.private = False
			elif mode == "s":
				c.secret = False
			elif mode == "t":
				c.optopic = False
			elif mode == "k":
				c.key = None
			elif mode == "l":
				c.limit = None
			elif mode == "I":
				c._invitelist.pop(arg, None)
			elif mode in self.prefixmap.voicecmds:
				try: c._voices.remove(arg)
				except KeyError: pass

	def _settopic(self, channel, newtopic, nick=None, ident=None, host=None, hostmask=None):
		self._channels[channel]._settopic(newtopic, nick, ident, host, hostmask=None)
		
	def _addusers(self, channel, users):
		for nick in users:
			prefix = nick[0]
			if prefix in self.prefixmap.nickprefixes:
				nick = nick.lstrip(self.prefixmap.nickprefixes)
				
			self._userjoin(channel, nick)
			if prefix in self.prefixmap.opprefixes:
				self._channels[channel]._ops.add(nick)
			if prefix in self.prefixmap.voiceprefixes:
				self._channels[channel]._voices.add(nick)
