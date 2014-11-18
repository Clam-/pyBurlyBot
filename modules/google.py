# Google services
# require APIkey module option

# TODO: maybe implement some of these neat filters:
# https://developers.google.com/custom-search/json-api/v1/reference/cse/list#request

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from json import load

from traceback import format_exc
		
OPTIONS = {
	"API_KEY" : (unicode, "API key for use with Google services.", u"not_a_key"),
	"CSE_ID" : (unicode, "ID of Custom Search Engine to use with Google search.", u"not_an_ID"),
}

URL = "https://www.googleapis.com/customsearch/v1?%s"
API_KEY = None
CSE_ID = None

# title: snippet (url)
RESULT_SPELL_TEXT = "(SP: %s?) {0}: {1} (%s)"
RESULT_TEXT = "{0}: {1} (%s)"

RESULTS_SPELL_IMG = "(SP: %s?) {0}{1}{2}{3}"
RESULTS_IMG = "{0}{1}{2}{3}"
# title (url)
RESULT_IMG = "%s (%s)"
RESULT_IMG2 = ", %s (%s)"

NUM_IMGS = 4

def google(event, bot):
	""" google searchterm. Will search Google using the provided searchterm."""
	if not event.argument: return bot.say(functionHelp(google))
	d = { "q" : event.argument.encode("utf-8"), "key" : API_KEY, "cx" : CSE_ID, "num" : 1,
		"fields" : "spelling/correctedQuery,items(title,link,snippet)" }
		
	f = urlopen(URL % (urlencode(d)))
	gdata = load(f)
	if f.getcode() == 200:
		if "items" in gdata:
			item = gdata["items"][0]
			snippet = item["snippet"].replace(" \n", " ")
			snippet = snippet
			if "spelling" in gdata:
				rpl = RESULT_SPELL_TEXT % (gdata["spelling"]["correctedQuery"], item["link"])
			else:
				rpl = RESULT_TEXT % item["link"]
			bot.say(rpl, fcfs=True, strins=[item["title"],snippet])
		else:
			if "spelling" in gdata:
				bot.say("(SP: %s) No results found." % gdata["spelling"]["correctedQuery"])
			else:
				bot.say("No results found.")
	else:
		bot.say("Error: %s" % (gdata))

def google_image(event, bot):
	""" gis searchterm. Will search Google images using the provided searchterm."""
	if not event.argument: return bot.say(functionHelp(google))
	d = { "q" : event.argument, "key" : API_KEY, "cx" : CSE_ID, "num" : NUM_IMGS, "searchType" : "image",
		"fields" : "spelling/correctedQuery,items(title,link)"}
		#TODO: consider displaying img stats like file size and resolution?
	try:
		f = urlopen(URL % (urlencode(d)))
		gdata = load(f)
		if f.getcode() == 200:
			if "items" in gdata:		
				entries = []
				# TODO: the following should probably be handled in the smart unicode cropping thing
				#	or in a smarter generic result splitter thing.
				for item in gdata["items"]:
					if entries:
						entries.append(RESULT_IMG2 % (item['title'], item['link']))
					else:
						entries.append(RESULT_IMG % (item['title'], item['link']))
				if len(entries) < NUM_IMGS: entries = entries+[""]*(NUM_IMGS-len(l))
				
				if "spelling" in gdata:
					bot.say(RESULTS_SPELL_IMG % gdata["spelling"]["correctedQuery"], fcfs=True, strins=entries)
				else:
					bot.say(RESULTS_IMG, fcfs=True, strins=entries)
			else:
				if "spelling" in gdata:
					bot.say("(SP: %s) No results found." % gdata["spelling"]["correctedQuery"])
				else:
					bot.say("No results found.")
		else:
			bot.say("Error: %s" % (gdata))
	except HTTPError, e:
		bot.say("Request error: %s" % e)
		raise
	except Exception, e: 
		bot.say("Error: %s" % (format_exc(2).replace("\n", ". ")))
		raise

def init(bot):
	global API_KEY # oh nooooooooooooooooo
	global CSE_ID # oh nooooooooooooooooo
	API_KEY = bot.getOption("API_KEY", module="google")
	CSE_ID = bot.getOption("CSE_ID", module="google")
	return True

#mappings to methods
mappings = (Mapping(command=("google", "g"), function=google),Mapping(command="gis", function=google_image),)
