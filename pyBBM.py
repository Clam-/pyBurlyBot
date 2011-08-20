#lol based heavily on the irclogbot example

# twisted imports
from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.threads import deferToThread
from twisted.python import log

# system imports
from time import asctime, time, localtime
from os.path import join
from sys import stdout
#bbm imports
from settings import Settings

class Event:
	def __init__(self, type=None, args=None, data=None, user=None, channel=None, msg=None, modes=None, setting=None):
		self.type = type
		self.args = args
		self.data = data #misc used for stuff like created(self, when), and myInfo(self, servername, version, umodes, cmodes), etc
		#I wonder if we can merge args and data
		#should use this for one of the kickee or kicker
		self.user = user
		self.channel = channel
		self.msg = msg
		self.modes = modes
		self.setting = setting #True for + modes
		
#dispatcher should have a HOST->list of modules mapping which then gets turn into a HOST->list of mappings
# when requesting a dispatch, depending on the botinst.host, will determine what set of mappings are checked.
# this allows only certain modules per server

class Dispatcher:
	def __init__(self, modules):
		self.modules = modules
		self.hostmap = {}
		#mapping from friendlyname => list I guess
		# have seperate mappings for speed?
		self.commandmapping = {}
		self.textmapping = {}
		self.mappings = {}
	
	def addhostmodules(self, name, modules):
		self.modules.update(modules)
		self.hostmap[name] = modules
		
	def reload(self, callback=None):
		print "LOADING..."
		#reload all modules I guess
		self.commandmapping = {}
		self.textmapping = {}
		self.mappings = {}
		notloaded = []
		from imp import find_module, load_module
		for mod in self.modules:
			try:
				(f, pathname, description) = find_module(mod, [join(Settings.cwd, "modules")])
				try:
					module = load_module(mod, f, pathname, description)
				except Exception as e:
					notloaded.append((mod, str(e)))
					f.close()
					continue
			except Exception as e:
				notloaded.append((mod, str(e)))
				continue
			
			module.init(Settings.dbQueue)
			#do stuff with module.mappings
			self.mappings[mod] = []
			for mapping in module.mappings:
				self.mappings[mod].append(mapping)
		
		if notloaded: print "WARNING: MODULE(S) NOT LOADED: %s" % notloaded
		else: print "All done."
		
	
	#event should be Event instance
	def dispatch(self, botinst, event):
		name = botinst.factory.server.name
		msg = event.msg
		command = ""
		if msg and msg.startswith(Settings.commandprefix):
			command = msg.split(" ", 1)[0][1:]
		#check for type match first:
		for module in self.mappings:
			if module in self.hostmap[name]:
				for mapping in self.mappings[module]:
					if "ALL" in mapping.type or event.type in mapping.type:
						#type match
						if mapping.command == None and mapping.regex == None:
							#dispatch asap
							self._dispatchreally(mapping.function, event, botinst)
						#check command, then check text
						elif msg:
							if mapping.command and (command == mapping.command):
								#dispatch
								self._dispatchreally(mapping.function, event, botinst)
							elif mapping.regex and (mapping.regex.match(msg)):
								self._dispatchreally(mapping.function, event, botinst)			
						
	def _dispatchreally(self, func, event, botinst):
		d = deferToThread(func, event, botinst, Settings.dbQueue)
		#add callback and errback
		d.addCallbacks(botinst.moduledata, botinst.moduleerr)

class BBMBot(IRCClient):
	"""BBM"""

	nickname = "testBBM"
	#lineRate = 1
	
	def connectionMade(self):
		IRCClient.connectionMade(self)
		#reset connection factory delay:
		self.factory.resetDelay()
		# do we restart the message queues here?
		#self.outbound = Queue() whatever

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		print "[disconnected at %s]" % asctime(localtime(time()))

	# callbacks for events

	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		print "[Signed on]"
		for chan in self.factory.server.channels:
			self.join(chan)
		Settings.dispatcher.dispatch(self, Event(type="signedOn"))

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		print "[I have joined %s]" % channel
		Settings.dispatcher.dispatch(self, Event(type="joined", channel=channel))

	def privmsg(self, user, channel, msg):
		"""This will get called when the bot receives a message."""
		user = user.split('!', 1)[0]
		print "<%s> %s" % (user, msg)
		Settings.dispatcher.dispatch(self, Event(type="privmsg", user=user, channel=channel, msg=msg))

	def action(self, user, channel, msg):
		"""This will get called when the bot sees someone do an action."""
		user = user.split('!', 1)[0]
		print "* %s %s" % (user, msg)
		Settings.dispatcher.dispatch(self, Event(type="action", user=user, channel=channel, msg=msg))

	def userRenamed(self, oldname, newname):
		"""Called when an IRC user changes their nickname."""
		print "%s is now known as %s" % (oldname, newname)
		Settings.dispatcher.dispatch(self, Event(type="userRenamed", user=oldname, data=newname))

	
	#def myInfo(self, servername, version, umodes, cmodes):
		#We could always use this to get server hostname
		
	# override the method that determines how a nickname is changed on
	# collisions. The default method appends an underscore.
	#Just kidding
	# def alterCollidedNick(self, nickname):
		
	#callback to handle module returns
	#do we sanitize input? lol what input
	def moduledata(self, result):
		pass
	
	def moduleerr(self, data):
		print "error:", data



class BBMBotFactory(ReconnectingClientFactory):
	"""A factory for BBMBot.
	A new protocol instance will be created each time we connect to the server.
	"""

	# the class of the protocol to build when new connection is made
	protocol = BBMBot

	def __init__(self, serversettings):
		#reconnect settings
		self.server = serversettings
		self.maxDelay = 60
		self.factor = 1.6180339887498948
	
	# def buildProtocol(self, address):
		# proto = ReconnectingClientFactory.buildProtocol(self, address)
		# self.dispatcher.botinst = proto
		# return proto



if __name__ == '__main__':
	# initialize logging
	log.startLogging(stdout)
	
	#setup dispatcher
	Settings.dispatcher = Dispatcher(Settings.modules)
	# create factory protocol and application
	#f = BBMBotFactory(sys.argv[1], sys.argv[2])
	for servername in Settings.servers:
		server = Settings.servers[servername]
		server.f = BBMBotFactory(server)
		Settings.dispatcher.addhostmodules(server.name, server.modules)
	
	#start db thread:
	Settings.dbThread.start()
	Settings.dispatcher.reload()
	
	for servername in Settings.servers:
		server = Settings.servers[servername]
		# connect factory to this host and port
		reactor.connectTCP(server.host, server.port, server.f)
	
	# run bot
	reactor.run()
	Settings.dbQueue.put("STOP")
	Settings.dbThread.join()
