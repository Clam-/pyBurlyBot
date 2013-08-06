from twisted.words.protocols.irc import CHANNEL_PREFIXES

class Event:
	def __init__(self, type, prefix, params, args=None, hostmask=None, channel=None, msg=None):
		self.type = type
		# Consider args as a dict of uncommon event attributes
		self.prefix = prefix
		self.params = params
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
		self.channel = channel
		# TODO: handle non-UTF8 cases
		#  probably by just trying a few different encodes and then giving up?
		if msg is not None: self.msg = msg.decode("utf-8") 
		else: self.msg = ""
		# Set by dispatcher, for convenience in module
		self.command = None
		self.input = None
	
	# we could check if target is equal to our nick (we don't even have our own nick available here, it's in botinst)
	#  or just check if doesn't start with "#"
	# TODO: Should this be called "isQuery" ?
	def isPM(self):
		return self.channel[0] not in CHANNEL_PREFIXES

class WaitEvent:
	def __init__(self, interestede, stope):
		self.done = False
		self.q = Queue()
		self.interestede = set(interestede)
		self.stope = set(stope)
		self.id = uuid1()	
