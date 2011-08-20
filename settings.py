#settings and stuff
from os import getcwdu
from db import DBaccess
from Queue import Queue


class Settings:
	nick = "testBBM"
	modules = set(["core", "samplemodule"])
	servers = {}
	cwd = getcwdu()
	commandprefix = "!"
	dbQueue = Queue()
	dbThread = DBaccess(dbQueue)
	
	@staticmethod
	def addServer(server):
		Settings.servers[server.name] = server
	
class Server:
	def __init__(self, name, host, port, channels, modules=None):
		self.name = name
		self.host = host
		self.port = port
		self.channels = channels
		if modules:
			self.modules = set(modules)
		else:
			self.modules = Settings.modules
			
Settings.addServer(Server("rizon", "irc.rizon.net", 6667, ["#lololol"]))