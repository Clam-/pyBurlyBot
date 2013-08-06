#settings and stuff
from os import getcwdu
from os.path import join, exists
from copy import copy
from Queue import Queue
from json import dump, load, JSONEncoder
from collections import MutableSet, OrderedDict
#bbm
from util.db import DBaccess
from util.libs import OrderedSet

KEYS_COMMON = ("nick", "nicksuffix", "commandprefix", "admins")
KEYS_SERVER = ("serverlabel",) + KEYS_COMMON + ("host", "port", "channels", "allowmodules", "denymodules")
KEYS_SERVER_SET = set(KEYS_SERVER)
KEYS_MAIN = KEYS_COMMON + ("modules", "datafolder", "datafile", "console", "servers")
KEYS_MAIN_SET = set(KEYS_MAIN)
#keys to create a copy of so no threading bads
KEYS_COPY = ("admins", "channels", "allowmodules", "denymodules", "modules")
#keys to deny getOption for:
KEYS_DENY = ("servers")

EXAMPLE_OPTS = {
	"serverlabel" : "Example Server",
	"host" : "irc.domain.tld",
	"channels" : ["#channel1", "#channel2"],
}

EXAMPLE_OPTS2 = {
	"serverlabel" : "Example Server 2",
	"host" : "irc.domain.tld",
	"port" : "+7001",
	"channels" : ["#channel1", ["#channel2", "password"]],
}

class ConfigException(Exception):
    pass

class Server(object):

	def __init__(self, opts, old=None):
		self.state = None
		self.serverlabel = opts.get("serverlabel", None)
		if not self.serverlabel:
			raise ConfigException("Missing serverlabel" % self.serverlabel)

		if "nick" in opts:
			self.nick = opts["nick"].encode('utf-8')

		if "nicksuffix" in opts:
			self.nicksuffix = opts["nicksuffix"].encode('utf-8')

		self.host = opts.get("host", None)
		if not self.host:
			raise ConfigException("%s must have a host" % self.serverlabel)
		
		self.port = opts.get("port", "6667")

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
		
		if "allowmodules" in opts:
			self.allowmodules = set(opts["allowmodules"])
		else: self.allowmodules = None
		if "denymodules" in opts:
			self.denymodules = set(opts["denymodules"])
		else: self.denymodules = None
		
		if old:
			self.state = old.state
			#convulted:
			self.state.container.settings = self
	
	def __getattr__(self, name):
		# get Server setting if set, else fall back to global Settings
		if name in self.__dict__: 
			return getattr(self, name)
		else:
			return getattr(Settings, name)
	
	def getOption(self, opt):
		if opt in KEYS_DENY: raise AttributeError("Access denied. (%s)" % opt)
		if opt in KEYS_COPY:
			return copy(getattr(self, opt))
		return getattr(self, opt)
	
	def setOption(self, opt, value, globalSetting=False):
		if not globalSetting:
			if opt not in KEYS_SERVER_SET:
				raise AttributeError("Server has no option: %s to set." % opt)
			else:
				setattr(self, opt, value)
		else:
			if opt not in KEYS_MAIN_SET:
				raise AttributeError("Settings has no option: %s to set." % opt)
			else:
				setattr(Settings, opt, value)
	
	def getModuleOption(self, module, option):
		return Settings.getModuleOption(module, option, self.serverlabel)
	
	def setModuleOption(self, module, option, value, globalSetting=False):
		if globalSetting:
			Settings.setModuleOption(module, option, value)
		else:
			Settings.setModuleOption(module, option, value, self.serverlabel)
	
	def _getDict(self):
		d = OrderedDict()
		for key in KEYS_SERVER:
			if key in self.__dict__:
				value = getattr(self, key)
				if value: 
					#preprocess channels
					if key == "channels":
						channels = []
						for channel in value:
							if len(channel) == 1:
								channels.append(channel[0])
							else:
								channels.append(channel)
						d[key] = channels
					else:
						d[key] = value
		return d

class SettingsBase:
	nick = "pyBBM"
	nicksuffix = "_"
	commandprefix = "!"
	datafolder = "data"
	datafile = "bbm.db"
	console = True
	modules = OrderedSet(["core"])
	admins = []
	servers = {}
	cwd = getcwdu()
	configfile = None
	moduleopts = {}
	moduledict = {}
	
	def _loadsettings(self):
		# TODO: need some exception handling for loading JSON
		try:
			newsets = load(open(self.configfile, "rb"))
		except ValueError as e:
			raise ConfigException("Config file (%s) contains errors: %s" % (self.configfile, e))
		
		# Only look for options we care about
		for opt in KEYS_MAIN:
			if opt in newsets:
				if opt == "servers":
					# Create servers and put them in the server map
					for serveropts in newsets["servers"]:
						if "serverlabel" not in serveropts: 
							raise ConfigException("Missing serverlabel in config.")
						label = serveropts["serverlabel"]
						if label in self.servers:
							server = self.servers[label]
							server = Server(serveropts, server)
						else:
							server = Server(serveropts)
						self.servers[server.serverlabel] = server
						
				elif opt == "modules":
					setattr(self, opt, OrderedSet(newsets[opt]))
				else:
					setattr(self, opt, newsets[opt])
		if "moduleoptions" in newsets:
			moduleopts = newsets["moduleoptions"]
	
	def reload(self):
		#restore "defaults"
		for key in KEYS_MAIN:
			setattr(self, key, getattr(SettingsBase, key))
				
		if self.configfile:
			#attempt to load user options
			self._loadsettings()
	
	def getModuleOption(self, module, option, server=None):
		if module in self.moduleopts:
			if server and server in self.moduleopts[module]["servers"]:
				return self.moduleopts[module]["servers"][server][option]
			else:
				return self.moduleopts[module][option]
				
	def setModuleOption(self, module, option, value, server=None):
		if module in self.moduleopts:
			if server and server in self.moduleopts[module]["servers"]:
				self.moduleopts[module]["servers"][server][option] = value
			else:
				self.moduleopts[module][option] = value
	
	def saveOptions(self):
		d = OrderedDict()
		for key in KEYS_MAIN:
			d[key] = getattr(self, key)
		if self.servers:
			d["servers"] = [serv._getDict() for serv in self.servers.values()]
		else:
			d["servers"] = [EXAMPLE_SERVER._getDict(), EXAMPLE_SERVER2._getDict()]
		dump(d, open(self.configfile, "wb"), indent=4, separators=(',', ': '), cls=ConfigEncoder)
		
	#should have some set option helper methods I guess

class ConfigEncoder(JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return list(obj)
		elif isinstance(obj, MutableSet):
			return list(obj)
		return JSONEncoder.default(self, obj)

Settings = SettingsBase()
EXAMPLE_SERVER = Server(EXAMPLE_OPTS)
EXAMPLE_SERVER2 = Server(EXAMPLE_OPTS2)