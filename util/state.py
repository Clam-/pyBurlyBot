#preliminary State

# State class should only be used for reading by modules, and setting from main event triggers, I guess

class Channel:
	
	def __init__(self, name, modes = None):
		self.name = name
		self.banlist = {} # [host] = (time, userwhosetban)
		self.users = {} # [user] = User
		self.modes = {} # [user] = modes, if user == "" then channel modes
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

class Network:
	
	def __init__(self, container):
		self.name = container.network
		container.state = self
		self.users = {} # [user] = User
		self.channels = {}
		self.container = container
	
	def nukenetwork(self, botinst):
		#clear channels
		self.channels = {}
		self.users = {}
		self.container._setBotinst(botinst)
		
	def nukechannel(self, channel):
		if channel in self.channels:
			for user in self.channels[channel].users:
				self.users[user].channels.remove(channel)
				if not self.users[user].channels:
					#user not known in any channels, remove existance
					del self.users[user]
	
	def joinchannel(self, channel):
		self.nukechannel(channel)
		self.channels[channel] = Channel(channel)

	def adduser(self, channel, user, hostmask=None):
		u = None
		if user not in self.users:
			u = User(user, hostmask)
			self.users[user] = u
		else:
			u = self.users[user]
		self.channels[channel].adduser(u)
		
	def addban(self, channel, ban, stuff):
		# TODO: lol do this
		pass
		
	def changeuser(self, oldnick, newnick):
		user = self.users[oldnick]
		del self.users[oldnick]
		self.users[newnick] = user
		#lol go through channels user is on
		for chan in user.channels:
			self.channels[chan].changeuser(oldnick, newnick)
			
	def removeuser(self, channel, user):
		if user in self.users:
			u = self.users[user]
			self.channels[channel].removeuser(u)
			if not u.channels:
				#user not known in any channels, remove existance
				del self.users[user]
		else:
			print "WARNING: user (%s) was never known about... SPOOKY" % user
		
		
def addnetwork(settings, container):
	settings.state = Network(container)


	
