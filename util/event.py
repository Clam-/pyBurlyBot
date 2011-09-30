class Event:
	def __init__(self, type=None, args=None, hostmask=None, channel=None, msg=None):
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
		# I think module should distinguish (if channel==user) this is a real PM	-Clam
		self.channel = channel
		if msg: self.msg = msg.decode("utf-8")
		else: self.msg = msg
		# Set by dispatcher, for convenience in module
		self.command = None
		self.input = None
	
	#let's do convenience stuff after all:
	#inside wrapper

class WaitEvent:
	def __init__(self, interestede, stope):
		self.done = False
		self.q = Queue()
		self.interestede = set(interestede)
		self.stope = set(stope)
		self.id = uuid1()	
