#lol based heavily on the irclogbot example

# twisted imports
from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.internet.threads import deferToThread
from twisted.python import log

# system imports
from time import asctime, time, localtime
from os import getcwdu
from os.path import join
from sys import stdout

class Server:
	def __init__(self, host, port, channels):
		self.host = host
		self.port = port
		self.channels = channels

class Settings:
	nick = "testBBM"
	servers = [Server("irc.rizon.net", 6667, ["#lololol"])]
	modules = ["samplemodule"]
	cwd = getcwdu()

class Dispatcher:
	def __init__(self, modules):
		self.modules = modules
		self.items = []
		self.botinst = None
		
	def reload(self, callback=None):
		print "LOADING..."
		#reload all modules I guess
		self.items = []
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
			except Exception as e:
				notloaded.append((mod, str(e)))
			#do stuff with module.mapping
			type, regex, function = module.mapping
			self.items.append((type, regex, function))
			
	def dispatch(self, type, data):
		if not self.botinst:
			print "THIS SHOULDN'T HAPPEN"
			return
		print self.items
		for item in self.items:
			if "ALL" in item[0] or type in item[0]:
				print "DISPATCHING?"
				if item[1].match(data["msg"]):
					print "DISPATCHING!"
					#dispatch
					d = deferToThread(item[2], type, data)
					#add callback and errback
					d.addCallbacks(self.botinst.moduledata, self.botinst.moduleerr)
			

class BBMBot(IRCClient):
	"""BBM"""

	nickname = "testBBM"

	def connectionMade(self):
		IRCClient.connectionMade(self)
		# do we restart the message queues here?
		#self.outbound = Queue() whatever

	def connectionLost(self, reason):
		IRCClient.connectionLost(self, reason)
		print "[disconnected at %s]" % asctime(localtime(time()))


	# callbacks for events

	def signedOn(self):
		"""Called when bot has succesfully signed on to server."""
		for chan in self.factory.channels:
			self.join(chan)

	def joined(self, channel):
		"""This will get called when the bot joins the channel."""
		print "[I have joined %s]" % channel

	def privmsg(self, user, channel, msg):
		"""This will get called when the bot receives a message."""
		user = user.split('!', 1)[0]
		print "<%s> %s" % (user, msg)
		
		# Check to see if they're sending me a private message
		#do we do let modules do this? Or should we define this as a "type" of message
		#if channel == self.nickname:
			#pm

		self.factory.dispatcher.dispatch("MSG", {"user" : user, "channel" : channel, "msg" : msg})

	def action(self, user, channel, msg):
		"""This will get called when the bot sees someone do an action."""
		user = user.split('!', 1)[0]
		print "* %s %s" % (user, msg)
		self.factory.dispatcher.dispatch("ACTION", {"user" : user, "channel" : channel, "msg" : msg})
		

	def irc_NICK(self, prefix, params):
		"""Called when an IRC user changes their nickname."""
		old_nick = prefix.split('!')[0]
		new_nick = params[0]
		print "%s is now known as %s" % (old_nick, new_nick)


	# override the method that determines how a nickname is changed on
	# collisions. The default method appends an underscore.
	#Just kidding
	# def alterCollidedNick(self, nickname):
		# """
		# Generate an altered version of a nickname that caused a collision in an
		# effort to create an unused related name for subsequent registration.
		# """
		# return nickname + '^'
		
	#callback to handle module returns
	#do we sanitize input?
	#def moduledata(self, type, data):
	def moduledata(self, result):	
		type, data = result
		print type, data
		if type == "MSG":
			self.msg(data["dest"], data["msg"])
		elif type == "ACTION":
			self.describe(data["dest"], data["msg"])
		elif type == "NOTICE":
			self.notice(data["dest"], data["msg"])
	
	def moduleerr(self, data):
		print "error:", data



class BBMBotFactory(ClientFactory):
	"""A factory for BBMBot.
	A new protocol instance will be created each time we connect to the server.
	"""

	# the class of the protocol to build when new connection is made
	protocol = BBMBot

	def __init__(self, channels, modules):
		self.channels = channels
		#setup dispatcher I guess
		self.dispatcher = Dispatcher(modules)
		self.dispatcher.reload()
	
	def buildProtocol(self, address):
		proto = ClientFactory.buildProtocol(self, address)
		self.dispatcher.botinst = proto
		return proto
	
	def clientConnectionLost(self, connector, reason):
		"""If we get disconnected, reconnect to server."""
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "connection failed:", reason
		reactor.stop()


if __name__ == '__main__':
	# initialize logging
	log.startLogging(stdout)

	#setup dispatcher
	
	# create factory protocol and application
	#f = BBMBotFactory(sys.argv[1], sys.argv[2])
	for server in Settings.servers:
		
		f = BBMBotFactory(server.channels, Settings.modules)
		# connect factory to this host and port
		reactor.connectTCP(server.host, server.port, f)

	# run bot
	reactor.run()
