#settings and stuff
from os import getcwdu
from os.path import join, exists
from Queue import Queue
from json import load
#bbm
from util.db import DBaccess
from util.libs import OrderedSet

class Server:
	nameless_server_count = 0
	ALLOWED_SETTINGS = set(["name", "nick", "nicksuffix", "host", "port", "channels", "allowmodules", "denymodules", "commandprefix" ])
	
	def __init__(self, opts):
		filteredopts = {}
		for setting in Server.ALLOWED_SETTINGS:
			try: filteredopts[setting] = opts[setting]
			except KeyError: pass
		opts = filteredopts
		
		try:
			self.name = opts["name"]
		except KeyError:
			Server.nameless_server_count += 1
			self.name = "Unnamed Server %d" % Server.nameless_server_count

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
						self.channels.append(channel[0].encode('utf-8'))
				else:
					self.channels.append(channel.encode('utf-8'))
		# TODO log warning if empty channels?
		
		if "allowmodules" in opts:
			self.allowmodules = set(opts["allowmodules"])
		else: self.allowmodules = None
		if "denymodules" in opts:
			self.denymodules = set(opts["denymodules"])
		else: self.denymodules = None
		# Should all servers store modules?
		# Maybe have include/exclude module lists instead?

	def __getattr__(self, name):
		if name in self.__dict__:
			return self.__dict__[name]
		return Settings.__dict__[name]

class Settings:
	nick = "nick"
	nicksuffix = "_"
	modules = OrderedSet([])
	servers = {}
	cwd = getcwdu()
	commandprefix = "!"
	dbQueue = Queue()
	dbThread = DBaccess(dbQueue)
	configfile = None
	moduleopts = {}
	moduledict = {}
	
	loadable = set(["nick", "modules", "servers", "commandprefix", "nicksuffix"])
	
	@classmethod
	def _loadsettings(cls, filename):
		newsets = load(open(filename, "rb"))
		for opt in cls.loadable:
			if opt in newsets:
				if opt == "servers":
					for serveropts in newsets["servers"]:
						server = Server(serveropts)
						cls.servers[server.name] = server
				elif opt == "nick": 
					cls.__dict__[opt] = newsets[opt].encode("utf-8")
				elif opt == "modules":
					cls.__dict__[opt] = OrderedSet(newsets[opt])
				elif opt == "nicksuffix":
					cls.__dict__[opt] = newsets[opt].encode("utf-8")
				else:
					cls.__dict__[opt] = newsets[opt]
	
	@classmethod
	def reload(cls):
		#load defaults.json, then override with user options
		cls._loadsettings(join(cls.cwd, "defaults.json"))
				
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
	
