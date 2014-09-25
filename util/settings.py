#settings and stuff
from os.path import join, exists
# TODO: is channels safe to shallow copy? (for example channel with password, I don't think so)
from copy import deepcopy
from Queue import Queue
from json import dump, load, JSONEncoder
from collections import MutableSet, OrderedDict
#BurlyBot
from util.libs import OrderedSet
from util.container import Container
from util.dispatcher import Dispatcher

KEYS_COMMON = ("altnicks", "encoding", "nick", "nickservpass", "nicksuffix", "commandprefix", "admins", "moduleopts")
KEYS_SERVER = ("serverlabel",) + KEYS_COMMON + ("host", "port", "channels", "allowmodules", "denymodules")
KEYS_SERVER_SET = set(KEYS_SERVER)
KEYS_MAIN = KEYS_COMMON + ("console", "debug", "datadir", "datafile", "enablestate", "modules", "servers")
KEYS_MAIN_SET = set(KEYS_MAIN)
#keys to create a copy of so no threading bads
KEYS_COPY = set(("admins", "channels", "allowmodules", "denymodules", "modules"))
#keys to deny getOption for:
KEYS_DENY = set(("servers", "dispatcher", "moduleopts"))
# TODO: this may be incomplete
# list of module setting types to copy to make sure no thread bads
TYPE_COPY = set((list, tuple, dict))

OPTION_DESC = {
	"altnicks" : "nicknames to be tried when desired nick is in use/unavailable.",
	"encoding" : "encoding to be used for sending and received messages.",
	"nick" : "nickname to be used.",
	"nickservpass" : "password to be send to nickserv on connect.",
	"nicksuffix" : "suffix to be appended to nick when nick is in use/unavailable.",
	#TODO: populate the rest of this.
}

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
	
class NoDefault(object):
	pass

class BaseServer(object):
	moduleopts = None # {}
	
	def __init__(self, opts):
		self.state = None
		self.moduleopts = {}
		self.setup(opts)
		
	def setup(self, opts):
		self.channels = []
		for key in KEYS_SERVER:
			opt = opts.get(key, None)
			if key == "serverlabel":
				if opt is None:
					raise ConfigException("Missing serverlabel.")
				elif ":" in opt:
					raise ConfigException('serverlabel ($s) cannot contain ":"' % self.serverlabel)
			elif key == "host" and opt is None:
				raise ConfigException("%s must have a host" % self.serverlabel)
			
			if key == "altnicks":
				self.altnicks = opt if isinstance(opt, list) else (opt,)
			elif key == "port":
				#process port number with SSL prefix
				#TODO: should we have a server config attribute called "ssl" instead?
				opt = opt if opt else "6667"
				if isinstance(opt, int):
					self.ssl = False
				elif opt.startswith("+"):
					opt = opt[1:]
					self.ssl = True
				else:
					self.ssl = False
				self.port = int(opt)
			elif key == "channels":
				if opt:
					for channel in opt:
						if isinstance(channel, list):
							if len(channel) > 1 and channel[1]:
								self.channels.append((channel[0], channel[1]))
							else:
								self.channels.append((channel[0],))
						else:
							self.channels.append((channel,))
		
			elif key == "allowmodules":
				self.allowmodules = set(opt) if opt else set([])
			elif key == "denymodules":
				self.denymodules = set(opt) if opt else set([])
			elif opt:
				setattr(self, key, opt)
		
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
					elif key == "port":
						d[key] = value if not getattr(self, "ssl") else "+"+str(value)
					else:
						d[key] = value
		return d
		
class DummyServer(BaseServer):
	def __init__(self, opts):
		BaseServer.__init__(self, opts)

class Server(BaseServer):
	
	def __init__(self, opts):
		BaseServer.__init__(self, opts)
		#dispatcher placeholder (probably not needed)
		self.dispatcher = None
		self.container = Container(self)

	def initializeDispatcher(self):
		# this should only be done once.
		assert self.dispatcher is None
		#create dispatcher:
		self.dispatcher = Dispatcher(self)
		
	def __getattr__(self, name):
		# get Server setting if set, else fall back to global Settings
		if name in self.__dict__: 
			return getattr(self, name)
		else:
			return getattr(Settings, name)
			
	# if channel or server is set, retrieve for that specific thing.
	# if channel or server is False, retrieve "global" for that thing.
	# TODO: make sure this optimized as it can be
	def getOption(self, opt, module=None, channel=None, server=None, default=NoDefault, setDefault=True):
		if opt in KEYS_DENY: raise AttributeError("Access denied. (%s)" % opt)
		if module:
			if server or server is None:
				# try searching for option in a server object
				if not server is None:
					try: moduleopts = Settings.servers[server].moduleopts
					except KeyError:
						raise AttributeError("Server (%s) not found" % server)
				else:
					moduleopts = self.moduleopts
				if module in moduleopts:
					mod = moduleopts[module]
					if channel and "_channels" in mod and channel in mod["_channels"] and opt in mod["_channels"][channel]:
						value = mod["_channels"][channel][opt]
						if type(value) in TYPE_COPY: return deepcopy(value) # copy value if compound datatype
						else: return value
					if opt in mod:
						value = mod[opt]
						if type(value) in TYPE_COPY: return deepcopy(value) # copy value if compound datatype
						else: return value
			# fall back to global moduleopts (or server was False)
			moduleopts = Settings.moduleopts
			# duplicated code from above, micro-optimization because bad.
			if module in moduleopts:
				mod = moduleopts[module]
				if channel and "_channels" in mod and channel in mod["_channels"] and opt in mod["_channels"][channel]:
					value = mod["_channels"][channel][opt]
					if type(value) in TYPE_COPY: return deepcopy(value) # copy value if compound datatype
					else: return value
				if opt in mod:
					value = mod[opt]
					if type(value) in TYPE_COPY: return deepcopy(value) # copy value if compound datatype
					else: return value
			if default is NoDefault:
				raise AttributeError("No setting (%s) for module: %s" % (opt, module))
			else:
				if setDefault:
					moduleopts.setdefault(module, {})[opt] = default
				return default
		#non-module (core) options
		if server is None:
			server = self
		elif server:
			if not server in Settings.servers:
				raise AttributeError("Server label (%s) not found." % server)
			server = Settings.servers[server]
		
		if server and opt in KEYS_SERVER_SET:
			value = getattr(self, opt)
		else:
			if not server or server is self:
				if opt not in KEYS_MAIN_SET:
					raise AttributeError("Settings has no option: (%s) to get." % opt)
				else:
					value = getattr(Settings, opt)	
			else:
				#case where a server setting is specifically attempted to be got, but it's not in KEYS_SERVER
				# instead of falling back to KEYS_MAIN, raise error
				raise AttributeError("Server setting has no option: (%s) to get." % opt)
		if opt in KEYS_COPY: return deepcopy(value)
		else: return value
	
	def setOption(self, opt, value, module=None, channel=None, server=None):
		if opt in KEYS_DENY: raise AttributeError("Access denied. (%s)" % opt)
		if type(value) in TYPE_COPY: value = deepcopy(value) # copy value if compound datatype
		
		if module:
			if server or server is None:
				# try searching for option in a server object
				if not server is None:
					try: moduleopts = Settings.servers[server].moduleopts
					except KeyError:
						raise AttributeError("Server (%s) not found" % server)
				else:
					moduleopts = self.moduleopts
				mod = moduleopts.setdefault(module, {})
				if channel: 
					mod.setdefault("_channels", {}).setdefault(channel, {})[opt] = value
				mod[opt] = value
			# if server was False, (setting "global")
			moduleopts = Settings.moduleopts
			# duplicated code from above, micro-optimization because bad.
			mod = moduleopts.setdefault(module, {})
			if channel: 
				mod.setdefault("_channels", {}).setdefault(channel, {})[opt] = value
			mod[opt] = value
		else:
			if server is None:
				server = self
			elif server:
				if not server in Settings.servers:
					raise AttributeError("Server label (%s) not found." % server)
				server = Settings.servers[server]
			
			if server and opt in KEYS_SERVER_SET:
				setattr(self, opt, value)
			else:
				if not server or server is self:
					if opt not in KEYS_MAIN_SET:
						raise AttributeError("Settings has no option: (%s) to set." % opt)
					else:
						setattr(Settings, opt, value)	
				else:
					#case where a server setting is specifically attempted to be set, but it's not in KEYS_SERVER
					# instead of falling back to KEYS_MAIN, raise error
					raise AttributeError("Server settings has no option: (%s) to set." % opt)
				
	
	def getModuleOption(self, module, option):
		return Settings.getModuleOption(module, option, self.serverlabel)
	
	def setModuleOption(self, module, option, value, globalSetting=False):
		if globalSetting:
			Settings.setModuleOption(module, option, value)
		else:
			Settings.setModuleOption(module, option, value, self.serverlabel)
	
	def getModule(self, modname):
		if not self.isModuleAvailable(modname):
			raise ConfigException("Module (%s) is not available." % modname)
		else:
			return Dispatcher.MODULEDICT[modname]
	
	def isModuleAvailable(self, modname):
		return (modname not in self.denymodules) and (modname in Dispatcher.MODULEDICT)
		

class SettingsBase:
	nick = "BurlyBot"
	altnicks = None # []
	nicksuffix = "_"
	nickservpass = None
	commandprefix = "!"
	datadir = "data"
	debug = False
	datafile = "BurlyBot.db"
	enablestate = False
	encoding = "utf-8"
	console = True
	modules = None # OrderedSet(["core"])
	admins = None # []
	servers = None # {}
	botdir = None
	configfile = None
	moduleopts = None # {}
	moduledict = None # {}
	
	#TODO: not sure if the following is needed or not. Class.dict seems to behave strangely
	def _setDefaults(self):
		self.altnicks = []
		self.modules = OrderedSet(["core"])
		self.admins = []
		self.moduleopts = {}
		self.moduledict = {}
		
	def __init__(self):
		self.servers = {}
		self._setDefaults()

	def _loadsettings(self):
		# TODO: need some exception handling for loading JSON
		try:
			newsets = load(open(self.configfile, "r"))
		except ValueError as e:
			raise ConfigException("Config file (%s) contains errors: %s"
				"\nTry http://jsonlint.com/ and make sure no trailing commas." % (self.configfile, e))
		
		# Only look for options we care about
		for opt in KEYS_MAIN:
			if opt in newsets:
				if opt == "servers":
					# Create servers and put them in the server map
					for serveropts in newsets["servers"]:
						if "serverlabel" not in serveropts: 
							# TODO: instead of raise, create error and continue loading.
							raise ConfigException("Missing serverlabel in config.")
						label = serveropts["serverlabel"]
						if label in self.servers:
							#refresh server settings
							self.servers[label].setup(serveropts)
						else:
							self.servers[label] = Server(serveropts)
				elif opt == "modules":
					setattr(self, opt, OrderedSet(newsets[opt]))
				else:
					setattr(self, opt, newsets[opt])
	
	def reload(self):
		#restore "defaults"
		for key in KEYS_MAIN:
			if key == "servers": continue #never nuke servers
			setattr(self, key, getattr(SettingsBase, key))
		self._setDefaults()
				
		if self.configfile:
			#attempt to load user options
			self._loadsettings()
	
	def reloadDispatchers(self, firstRun=False):
		# Reset Dispatcher loaded modules
		Dispatcher.reset()
		for server in self.servers.itervalues():
			if firstRun:
				server.initializeDispatcher()
			else:
				server.dispatcher.reload()
		Dispatcher.showLoadErrors()
	
	def saveOptions(self):
		d = OrderedDict()
		for key in KEYS_MAIN:
			if key == "servers": continue
			val = getattr(self, key)
			if val:
				d[key] = val
		if self.servers:
			d["servers"] = [serv._getDict() for serv in self.servers.itervalues()]
		else:
			EXAMPLE_SERVER = DummyServer(EXAMPLE_OPTS)
			EXAMPLE_SERVER2 = DummyServer(EXAMPLE_OPTS2)
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
