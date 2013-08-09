#preliminary State

# State class should only be used for reading by modules, and setting from main event triggers, I guess

class Channel:
	
	def __init__(self, name, modes = None):
		self.name = name
		self.banlist = {} # [host] = (time, userwhosetban)
		self.users = {} # [nick] = User
		# TODO: Standify "modes". Is it a list? Of "@", "+", etc?
		#  in the case of channel modes, is it a list like ["+s", "+k pass"]?
		self.modes = {} # [nick] = modes, if nick == "" then channel modes
		self.topic = ""
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
		user.channels.remove(self.name)

class User:
	
	def __init__(self, nick, host=None):
		self.channels = set()
		self.nick = nick
		self.hostmask = host
		#maybe store more infos?

# TODO: function_renaming_cuz_conventions ~grifftask
class Network:
	def __init__(self, network):
		self.name = network
		self.users = {} # [nick] = User
		self.channels = {}
	
	def resetnetwork(self):
		#clear channels
		self.channels = {}
		self.users = {}
		
	def nukechannel(self, channel):
		if channel in self.channels:
			for user in self.channels[channel].users:
				self.users[user].channels.remove(channel)
				if not self.users[user].channels:
					#user not known in any channels, remove existance
					del self.users[user]
			del self.channels[channel]

	def nukeuser(self, nick):
		if nick in self.users:
			u = self.users[nick]
			for channel in self.channels:
				if nick in self.channels[channel].users:
					self.channels[channel].removeuser(u)
			del self.users[nick]

	def joinchannel(self, channel):
		self.nukechannel(channel)
		self.channels[channel] = Channel(channel)

	def leavechannel(self, channel):
		self.nukechannel(channel)

	def adduser(self, channel, nick, hostmask=None):
		u = None
		if nick not in self.users:
			u = User(nick, hostmask)
			self.users[nick] = u
		else:
			u = self.users[nick]
		self.channels[channel].adduser(u)

	def addban(self, channel, ban, stuff):
		# TODO: do this
		pass

	def changeuser(self, oldnick, newnick):
		user = self.users[oldnick]
		del self.users[oldnick]
		self.users[newnick] = user
		#go through channels user is on
		for chan in user.channels:
			self.channels[chan].changeuser(oldnick, newnick)

	def removeuser(self, channel, nick):
		if nick in self.users:
			u = self.users[nick]
			self.channels[channel].removeuser(u)
			if not u.channels:
				#user not known in any channels, remove existance
				del self.users[nick]
		else:
			print "WARNING: user (%s) was never known about... 2SPOOKY" % user



	
