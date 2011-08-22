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
from optparse import OptionParser

#bbm imports
from settings import Settings


class Event:
	def __init__(self, type=None, args=None, data=None, hostmask=None, channel=None, msg=None, modes=None, setting=None):
		self.type = type
		# Consider args as a dict of uncommon event attributes
		self.args = args
		self.hostmask = hostmask
		self.nick = None
		self.ident = None
		self.host = None
		if hostmask:
			try:
				nick, ident = hostmask.split('!', 1)
				ident, host = ident.split('@', 1)
			except ValueError:
				pass
			else:
				self.nick = nick
				self.ident = ident
				self.host = host
		# This can be a user, too. Should probably do something to distinguish
		self.channel = channel
		if msg: self.msg = msg.decode("utf-8")
		else: self.msg = msg
		# Should be args?
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
		for mod in modules:
			self.modules.add(mod)
		self.hostmap[name] = modules
		
	def reload(self, callback=None):
		print "LOADING..."
		moddir = join(Settings.cwd, "modules")
		#reload all modules I guess
		self.commandmapping = {}
		self.textmapping = {}
		self.mappings = {}
		notloaded = []
		from imp import find_module, load_module
		Settings.moduledict = {}
		for mod in self.modules:
			try:
				(f, pathname, description) = find_module(mod, [moddir])
				try:
					module = load_module(mod, f, pathname, description)
				except Exception as e:
					notloaded.append((mod, str(e)))
					f.close()
					continue
			except Exception as e:
				notloaded.append((mod, str(e)))
				continue
			
			try:
				if module.init(Settings.dbQueue):
					Settings.moduledict[mod] = module
					#do stuff with module.mappings
					self.mappings[mod] = []
					for mapping in module.mappings:
						self.mappings[mod].append(mapping)
				else:
					notloaded.append((mod, "Error in init()"))
			except Exception as e:
				notloaded.append((mod, "ERROR LOADING MODULE (%s): %s" % (mod, e)))
		
		if notloaded: print "WARNING: MODULE(S) NOT LOADED: %s" % notloaded
		else: print "All done."
		
	
	#event should be Event instance
	def dispatch(self, botinst, event):
		name = botinst.factory.server["name"]
		msg = event.msg
		command = ""
		if msg and msg.startswith(Settings.getOption("commandprefix", botinst.factory.server["name"])):
			#case insensitive match?
			#also this means that commands can't have spaces in them, and lol command prefix can't be a space
			command = msg.split(" ", 1)[0][1:].lower()
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

	#nickname = None
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
		for chan in self.factory.server["channels"]:
			if isinstance(chan, list):
				if len(chan) > 1: self.join(chan[0], chan[1])
				else: self.join(chan[0])
			else: self.join(chan)
		Settings.dispatcher.dispatch(self, Event(type="signedOn"))

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		print "[I have joined %s]" % channel
		Settings.dispatcher.dispatch(self, Event(type="joined", channel=channel))

	def privmsg(self, hostmask, channel, msg):
		"""This will get called when the bot receives a message."""
		print "<%s> %s" % (nick, msg)
		Settings.dispatcher.dispatch(self, Event(type="privmsg", hostmask=hostmask, channel=channel, msg=msg))

	def action(self, hostmask, channel, msg):
		"""This will get called when the bot sees someone do an action."""
		nick = hostmask.split('!', 1)[0]
		print "* %s %s" % (nick, msg)
		Settings.dispatcher.dispatch(self, Event(type="action", hostmask=hostmask, channel=channel, msg=msg))

	def irc_NICK(self, prefix, params):
		"""
		Called when a user changes their nickname.
		"""
		nick = string.split(prefix,'!', 1)[0]
		if nick == self.nickname:
			self.nickChanged(params[0])
		else:
			self.userRenamed(prefix, params[0])
		
	def userRenamed(self, hostmask, newname):
		"""Called when an IRC user changes their nickname."""
		print "%s is now known as %s" % (hostmask.split('!', 1)[0], newname)
		Settings.dispatcher.dispatch(self, Event(type="userRenamed", hostmask=hostmask, args={'newname': newname}))
	
	#overriding msg
	def msg(self, user, msg, length=None):
		msg = msg.encode("utf-8")
		if length: IRCClient.msg(self, user, msg, length)
		else: IRCClient.msg(self, user, msg)
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
	
	def moduleerr(self, e):
		print "error:", e #exception, or Failure thing



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
	
	def buildProtocol(self, address):
		proto = ReconnectingClientFactory.buildProtocol(self, address)
		proto.nickname = Settings.getOption("nick", self.server["name"])
		#Maybe add serversettings to the BBMBot instance here? Or leave it as instance.factory.server
		return proto



if __name__ == '__main__':
	from os.path import exists
	# initialize logging
	log.startLogging(stdout)
	
	parser = OptionParser(usage="usage: %prog [options] [configfile]")
	parser.add_option("-d", "--dummy", action="store_true", dest="dummy", default=None,
		help="Dummy option. Placeholder.")
	(options, args) = parser.parse_args()
	#get settings file
	settingsf = None
	if len(args) > 0:
		settingsf = args[0]
	
	#make settings object with defaults.json
	#then make settings object with options.json and converge somehow...
	# I've done this before ghetto style, but we'll see what happens. 
	#(okay it's going to be pretty different to what I've done before)
	if settingsf and exists(settingsf):
		Settings.configfile = settingsf
	else:
		print "Settings file not found, running with defaults..."
	Settings.reload()
	
	#setup dispatcher
	Settings.dispatcher = Dispatcher(Settings.modules)
	# create factory protocol and application
	#f = BBMBotFactory(sys.argv[1], sys.argv[2])
	for servername in Settings.servers:
		server = Settings.servers[servername]
		server["factory"] = BBMBotFactory(server)
		Settings.dispatcher.addhostmodules(servername, Settings.getOption("modules", server["name"]))
	
	#start db thread:
	Settings.dbThread.start()
	Settings.dispatcher.reload()
	
	for servername in Settings.servers:
		server = Settings.servers[servername]
		# connect factory to this host and port
		reactor.connectTCP(server["host"], server["port"], server["factory"])
	
	# run bot
	reactor.run()
	Settings.dbQueue.put("STOP")
	Settings.dbThread.join()
