from twisted.words.protocols.irc import CHANNEL_PREFIXES
from helpers import coerceToUnicode

from time import time

# NOTHING IN EVENT SHOULD BE MODIFIED BY MODULES EVER, THANKS.
# TODO: prefix and hostmask are I think always the same. What to do?
class Event:
	def __init__(self, type, prefix=None, params=None, hostmask=None, target=None, msg=None, 
		nick=None, ident=None, host=None, encoding="utf-8", command=None, argument=None, **kwargs):
		self.type = type
		# kwargs is a dict of uncommon event attributes
		self.prefix = prefix
		self.params = params
		self.hostmask = hostmask
		self.nick = coerceToUnicode(nick, encoding) if nick else nick
		self.ident = coerceToUnicode(ident, encoding) if ident else ident
		# Note: if unicode/punycode hostnames becomes a thing for IRC, .decode("idna") I guess
		self.host = host
		
		self.target = coerceToUnicode(target, encoding) if target else target
		
		# if there is a msg, it's already unicode (done in dispatcher.)
		self.msg = msg
		
		self.command = command
		self.argument = argument
		
		self.kwargs = kwargs
		
		# might be useful
		self.time = time()
	
	def __repr__(self):
		return "Event(type=%s, prefix=%s, params=%s, args=%s, hostmask=%s, nick=%s, " \
			"ident=%s, host=%s, target=%s, msg=%s, command=%s, argument=%s" % \
			(self.type, self.prefix, self.params, self.args, self.hostmask, self.nick,
				self.ident, self.host, self.target, self.msg, self.command, self.argument)
	
	# TODO: Should this be called "isQuery" ?
	def isPM(self):
		return self.target[0] not in CHANNEL_PREFIXES
