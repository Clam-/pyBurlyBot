#codings module
# for things like md5ing, rot13, urlencode, unquoting and so on
from hashlib import algorithms, md5, new
try:
	from hashlib import algorithms_available
except ImportError:
	algorithms_available = None
from zlib import crc32
from urllib import unquote, quote

from util import Mapping, argumentSplit, functionHelp

def hash(event, bot):
	""" hash method content. content will be hashed according to method (after encoding to UTF-8.) Use "hash methods" to see what methods are supported."""
	method, content = argumentSplit(event.argument, 2)
	if not (method and content):
		if method == "methods":
			if algorithms_available:
				return bot.say("Supported hash methods: %s" % ", ".join(algorithms_available))
			else:
				return bot.say("Supported hash methods: %s" % ", ".join(algorithms))
		return bot.say(functionHelp(hash))
	if (algorithms_available and (method not in algorithms_available)) or (not algorithms_available and method not in algorithms):
		return bot.say("Unknown method (%s). Use \x02hash methods\x02 to see what methods are supported.")
	h = new(method)
	h.update(content.encode("utf-8"))
	bot.say("%s - %s" % (h.hexdigest(), repr(content)))

def md5(event, bot):
	""" md5 content. content will be md5 hashed (after encoding to UTF-8.)"""
	arg = event.argument
	if not arg:
		return bot.say(functionHelp(md5))
	bot.say("%s - %s" % (md5(arg.encode("utf-8")).hexdigest(), repr(arg)))
	
def rot13(event, bot):
	""" rot13 content. content will be rot13 encoded."""
	arg = event.argument
	if not arg:
		return bot.say(functionHelp(rot13))
	bot.say(arg.encode("rot13", "ignore"))

def crc(event, bot):
	""" crc content. content will be crc32 encoded (after encoding to utf-8.)"""
	arg = event.argument
	if not arg:
		return bot.say(functionHelp(crc))
	bot.say("%x - %s" % (crc32(arg.encode("utf-8")) & 0xffffffff, repr(arg)))
	
def funquote(event, bot):
	""" unquote content. content will be URL decoded."""
	arg = event.argument
	if not arg:
		return bot.say(functionHelp(funquote))
	bot.say(unquote(str(arg)).decode("utf-8"))
	
def fquote(event, bot):
	""" quote content. content will be URL encoded."""
	arg = event.argument
	if not arg:
		return bot.say(functionHelp(fquote))
	bot.say(quote(arg.encode("utf-8")))
		
#mappings to methods
mappings = (Mapping(command="hash", function=hash), Mapping(command="md5", function=md5), Mapping(command="rot13", function=rot13),
	Mapping(command="crc", function=crc), Mapping(command="unquote", function=funquote), Mapping(command="quote", function=fquote),)