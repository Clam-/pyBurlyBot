#preliminary State

# State class should only be used for reading by modules, and setting from main event triggers, I guess
# maybe this should be in a database, for things like "search all bans on Y channel from Z user"
#  LOL After toying with mockups of this idea no. If you want a ban DB it should be a module I guess...

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
		#maybe store more infos? CTCPLOLVERSION?

class Network:
	
	def __init__(self, network):
		self.name = network
		self.users = {} # [user] = User
		self.channels = {}
		
class State:
	#dict of dict of dict sort of thing?
	# [network][channel/user] ? nope. classes.
	
	networks = {}
	
	#doing methods so we can do things like "if not exist, create"
	@classmethod
	def nukenetwork(cls, network):
		cls.networks[network] = Network(network)
	
	@classmethod
	def nukechannel(cls, network, channel):
		network = cls.networks[network]
		if channel in network.channels:
			for user in network.channels[channel].users:
				network.users[user].channels.remove(channel)
				if not network.users[user].channels:
					#user not known in any channels, remove existance
					del network[users][user]
					
		cls.networks[network.name].channels[channel] = Channel(channel)
	
	@classmethod
	def adduser(cls, network, channel, user, hostmask=None):
		network = cls.networks[network]
		u = None
		if user not in network.users:
			u = User(user, hostmask)
			network.users[user] = u
		else:
			u = network.users[user]
		network.channels[channel].adduser(u)
		
	@classmethod
	def addban(cls, network, channel, ban, stuff):
		# TODO: lol do this
		pass
		
	@classmethod
	def changeuser(cls, network, oldnick, newnick):
		network = cls.networks[network]
		user = network.users[oldnick]
		del network.users[oldnick]
		network.users[newnick] = user
		#lol go through channels user is on
		for chan in user.channels:
			network[chan].changeuser(oldnick, newnick)
			
	@classmethod
	def removeuser(cls, network, channel, user):
		network = cls.networks[network]
		if user in network.users:
			u = network.users[user]
			network.channels[channel].removeuser(u)
			if not u.channels:
				#user not known in any channels, remove existance
				del network.users[user]
		else:
			print "WARNING: user was never known about... SPOOKY"
		
		