from twisted.words.protocols.irc import CHANNEL_PREFIXES
from helpers import coerceToUnicode

#TODO: consider this, events should probably not be mutable 
# (can this be done? might have to trust modules not to do something stupid)
# TODO: prefix and hostmask are I think always the same. What to do?
class Event:
	def __init__(self, type, prefix=None, params=None, hostmask=None, target=None, msg=None, 
		nick=None, ident=None, host=None, **kwargs):
		self.type = type
		# kwargs is a dict of uncommon event attributes
		self.prefix = prefix
		self.params = params
		self.hostmask = hostmask
		self.nick = nick
		self.ident = ident
		self.host = host
		
		self.target = target
		
		if msg is not None: 
			self.msg = coerceToUnicode(msg)
		else: 
			self.msg = ""
		# Set by dispatcher, for convenience in module
		self.command = None
		
		self.argument = None
		self.kwargs = kwargs
	
	def __repr__(self):
		return "Event(type=%s, prefix=%s, params=%s, args=%s, hostmask=%s, nick=%s, " \
			"ident=%s, host=%s, target=%s, msg=%s, command=%s, argument=%s" % \
			(self.type, self.prefix, self.params, self.args, self.hostmask, self.nick,
				self.ident, self.host, self.target, self.msg, self.command, self.argument)
	
	# we could check if target is equal to our nick (we don't even have our own nick available here, it's in botinst)
	#  or just check if doesn't start with "#"
	# TODO: Should this be called "isQuery" ?
	def isPM(self):
		return self.target[0] not in CHANNEL_PREFIXES
