#settings and stuff
from os import getcwdu
from os.path import join, exists
from db import DBaccess
from Queue import Queue

from json import load
from util.libs import OrderedSet

class Settings:
	nick = "nick"
	modules = OrderedSet(["core", "samplemodule"])
	servers = {}
	cwd = getcwdu()
	commandprefix = "!"
	dbQueue = Queue()
	dbThread = DBaccess(dbQueue)
	configfile = None
	moduleopts = {}
	moduledict = {}
	
	loadable = set(["nick", "modules", "servers", "commandprefix"])
	
	@classmethod
	def addServer(cls, server):
		cls.servers[server.name] = server
	
	#this is kinda lame
	@staticmethod
	def deunicode(server):
		channels = server["channels"]
		for index in range(len(channels)):
			if isinstance(channels[index], list):
				channels[index][0] = channels[index][0].encode("utf-8")
				if len(channels[index]) > 1 and channels[index][1]:
					channels[index][1] = channels[index][1].encode("utf-8")
			else:
				channels[index] = channels[index].encode("utf-8")
		server["nick"] = server["nick"].encode("utf-8")
	
	@classmethod
	def _loadsettings(cls, filename):
		newsets = load(open(filename, "rb"))
		for opt in cls.loadable:
			if opt in newsets:
				if opt == "servers":
					for server in newsets[opt]:
						if server["name"] not in cls.servers:
							#create server object and assign,
							#let's keep everything as dicts for now, sry Griff
							cls.servers[server["name"]] = server
							cls.deunicode(server)
							if "modules" in server:
								server["modules"] = OrderedSet(server["modules"])
						else:
							for sopt in server:
								if sopt == "modules":
									cls.servers[server["name"]][sopt] = OrderedSet(server[sopt])
								else:
									cls.servers[server["name"]][sopt] = server[sopt]
								cls.deunicode(cls.servers[server["name"]])
				elif opt == "nick": 
					cls.__dict__[opt] = newsets[opt].encode("utf-8")
				elif opt == "modules":
					cls.__dict__[opt] = OrderedSet(newsets[opt])
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
	def getOption(cls, option, server=None):
		if server and (server in cls.servers) and (option in cls.servers[server]):
			return cls.servers[server][option]
		else:
			return cls.__dict__[option] #???
	
	@classmethod
	def getModuleOption(cls, module, option, server=None):
		if module in cls.moduleopts:
			if server and server in cls.moduleopts[module]["servers"]:
				return cls.moduleopts[module]["servers"][server][option]
			else:
				return cls.moduleopts[module][option]
		
	#should have some set option helper methods I guess
	
# class Server:
	# def __init__(self, name, host, port, channels, modules=None):
		# self.name = name
		# self.host = host
		# self.port = port
		# self.channels = channels
		# if modules:
			# self.modules = set(modules)
		# else:
			# self.modules = Settings.modules
			
# Settings.addServer(Server("rizon", "irc.rizon.net", 6667, ["#lololol"]))