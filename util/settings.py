#settings and stuff
from os import getcwdu
from os.path import join, exists
from Queue import Queue
from json import load
#bbm
from util.db import DBaccess
from util.libs import OrderedSet

class Server(object):
	name = "Server"
	nick = "nick"
	nicksuffix = "_"
	commandprefix = "!"

	def __init__(self, opts):
		self.state = None
		self.name = None
		try:
			self.name = opts["name"]
		except KeyError:
			pass
		if not self.name:
			self.name = "Unnamed Server"
		num = 2
		while self.name in Settings.servers:
			self.name = "%s%d" % (self.name, num)
			num += 1

		if "nick" in opts:
			self.nick = opts["nick"].encode('utf-8')

		if "nicksuffix" in opts:
			self.nicksuffix = opts["nicksuffix"].encode('utf-8')

		try:
			self.host = opts["host"]
		except KeyError:
			raise ValueError("%s must have a host" % self.name)
		try:
			self.port = opts["port"]
		except KeyError:
			# default?
			self.port = 6667

		if "commandprefix" in opts:
			self.commandprefix = opts["commandprefix"]

		self.channels = []
		if "channels" in opts:
			for channel in opts['channels']:
				if isinstance(channel, list):
					if len(channel) > 1 and channel[1]:
						self.channels.append(
							(channel[0].encode('utf-8'), 
							channel[1].encode('utf-8'))
							)
					else:
						self.channels.append((channel[0].encode('utf-8'),))
				else:
					self.channels.append((channel.encode('utf-8'),))
		# TODO log warning if empty channels?
		
		if "allowmodules" in opts:
			self.allowmodules = set(opts["allowmodules"])
		else: self.allowmodules = None
		if "denymodules" in opts:
			self.denymodules = set(opts["denymodules"])
		else: self.denymodules = None
		# Should all servers store modules?
		# Maybe have include/exclude module lists instead?]
	
	def getModuleOption(self, module, option):
		return Settings.getModuleOption(module, option, self.name)

class Settings:
	nick = "nick"
	nicksuffix = "_"
	modules = OrderedSet([])
	servers = {}
	cwd = getcwdu()
	configfile = None
	moduleopts = {}
	moduledict = {}
	
	loadable = set(["nick", "modules", "servers", "commandprefix", "datafolder", "datafile", "console", "nicksuffix"])
	
	@classmethod
	def _loadsettings(cls, filename, defaults=False):
		# TODO: need some exception handling for loading JSON
		newsets = load(open(filename, "rb"))
		for opt in cls.loadable:
			if opt in newsets:
				# This is kind of weird now, not sure what to do.
				# Server class seems right for those settings, so watev
				if opt == "servers":
					# Don't load default servers?
					if defaults:
						continue
					for serveropts in newsets["servers"]:
						server = Server(serveropts)
						cls.servers[server.name] = server
				elif opt == "nick": 
					setattr(Server, opt, newsets[opt].encode("utf-8"))
				elif opt == "nicksuffix":
					setattr(Server, opt, newsets[opt].encode("utf-8"))
				elif opt == "commandprefix":
					setattr(Server, opt, newsets[opt])
				elif opt == "modules":
					cls.__dict__[opt] = OrderedSet(newsets[opt])
				else:
					cls.__dict__[opt] = newsets[opt]
	
	@classmethod
	def reload(cls):
		#load defaults.json, then override with user options
		cls._loadsettings(join(cls.cwd, "defaults.json"), defaults=True)
				
		if cls.configfile:
			#attempt to load user options
			cls._loadsettings(cls.configfile)
		#load module options now?
		moddir = join(cls.cwd, "modules")
		for module in cls.modules:
			fname = join(moddir, "%s.json" % module)
			if exists(fname):
				cls.moduleopts[module] = load(open(fname, "rb"))
		
	#some helper methods
	@classmethod
	def getOption(cls, option):
		return cls.__dict__[option] #???
	
	@classmethod
	def getModuleOption(cls, module, option, server=None):
		if module in cls.moduleopts:
			if server and server in cls.moduleopts[module]["servers"]:
				return cls.moduleopts[module]["servers"][server][option]
			else:
				return cls.moduleopts[module][option]
		
	#should have some set option helper methods I guess
	
