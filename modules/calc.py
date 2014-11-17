#calc
# caved in and used wolframalpha. Didn't want to combine two services for currency and maths(mathjs was super tempting)

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from xml.etree.cElementTree import iterparse

from traceback import format_exc

OPTIONS = {
	"API_KEY" : (unicode, "API key (App ID) for use with WolframAlpha services.", u"not_an_id"),
}

API_KEY = None
URL = "http://api.wolframalpha.com/v2/query?%s"

def calc(event, bot):
	""" google searchterm. Will search Google using the provided searchterm."""
	if not event.argument: return bot.say(functionHelp(google))
	s = (("input", event.argument.encode("utf-8")), ("appid", API_KEY), ("reinterpret", "true"),
		("includepodid", "Input"), ("includepodid", "Result"), ("format", "plaintext"))
	# TODO: use "units" param in conjunction with calling user's location.
	
	try:
		f = urlopen(URL % (urlencode(s)))
		if f.getcode() == 200:
			# http://effbot.org/zone/element-iterparse.htm
			# get an iterable
			context = iterparse(f, events=("start", "end"))
			# get the root element
			ievent, root = context.next()
			
			input = None
			result = None
			error = ""
			pod = None
			for ievent, elem in context:
				if ievent == "start" and elem.tag == "pod":
					pod = elem.attrib["id"]
				elif ievent == "end" and elem.tag == "error":
					error += elem["msg"]
					#elem.clear()
				elif ievent == "end" and elem.tag == "plaintext":
					if pod == "Result":
						result = elem.text
					elif pod == "Input":
						input = elem.text
					#elem.clear()
				elif ievent == "end":
					pass
					#elem.clear()
			#root.clear()
			
			msg = "%s: " % event.nick
			if input:
				msg += "(%s) " % input
			if result:
				msg += "\x02%s\x02" % result
			if error:
				msg += " (Error: %s)" % error
			bot.say(msg)
		else:
			bot.say("Dunno.")
	except HTTPError, e:
		bot.say("Request error: %s" % e)
		raise
	except Exception, e: 
		bot.say("Error: %s" % (format_exc(2).replace("\n", ". ")))
		raise

def init(bot):
	global API_KEY # oh nooooooooooooooooo
	API_KEY = bot.getOption("API_KEY", module="calc")
	return True

#mappings to methods
mappings = (Mapping(command=("calc", "c"), function=calc),)
