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
	
	@staticmethod
	def addServer(server):
		Settings.servers[server.name] = server
	
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
	
	@staticmethod
	def _loadsettings(filename):
		newsets = load(open(filename, "rb"))
		for opt in Settings.loadable:
			if opt in newsets:
				if opt == "servers":
					for server in newsets[opt]:
						if server["name"] not in Settings.servers:
							#create server object and assign,
							#let's keep everything as dicts for now, sry Griff
							Settings.servers[server["name"]] = server
							Settings.deunicode(server)
							if "modules" in server:
								server["modules"] = OrderedSet(server["modules"])
						else:
							for sopt in server:
								if sopt == "modules":
									Settings.servers[server["name"]][sopt] = OrderedSet(server[sopt])
								else:
									Settings.servers[server["name"]][sopt] = server[sopt]
								Settings.deunicode(Settings.servers[server["name"]])
				elif opt == "nick": 
					Settings.__dict__[opt] = newsets[opt].encode("utf-8")
				elif opt == "modules":
					Settings.__dict__[opt] = OrderedSet(newsets[opt])
				else:
					Settings.__dict__[opt] = newsets[opt]
	
	@staticmethod
	def reload():
		#load defaults.json, then override with user options
		Settings._loadsettings(join(Settings.cwd, "defaults.json"))
				
		if Settings.configfile:
			#attempt to load user options
			Settings._loadsettings(Settings.configfile)
		#load module options now?
		moddir = join(Settings.cwd, "modules")
		for module in Settings.modules:
			fname = join(moddir, "%s.json" % module)
			if exists(fname):
				Settings.moduleopts[module] = load(open(fname, "rb"))
		
	#some helper methods
	@staticmethod
	def getOption(option, server=None):
		if server and (server in Settings.servers) and (option in Settings.servers[server]):
			return Settings.servers[server][option]
		else:
			return Settings.__dict__[option] #???
	
	@staticmethod		
	def getModuleOption(module, option, server=None):
		if module in Settings.moduleopts:
			if server and server in Settings.moduleopts[module]["servers"]:
				return Settings.moduleopts[module]["servers"][server][option]
			else:
				return Settings.moduleopts[module][option]
		
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