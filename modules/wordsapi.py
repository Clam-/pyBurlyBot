# word based API
# using Cambridge Dictionaries Online
# 
# require APIkey module option

from urllib2 import Request, urlopen, HTTPError
from urllib import quote, urlencode
from json import load
from xml.etree.cElementTree import iterparse
from util.settings import ConfigException
from cStringIO import StringIO

OPTIONS = {
	"API_KEY" : (unicode, "API key for use with Cambridge Dictionaries Online's services.", u""),
}

DICT_ORDER = [
	"dictionaries/british",
	"dictionaries/american-english",
]
	

# https://dictionary.cambridge.org/api/v1/dictionaries/british/entries/toilet/?format=html
SEARCH_URL = "https://dictionary.cambridge.org/api/v1/%s/entries/%s/?format=xml"
DIDYOUMEAN_URL = "https://dictionary.cambridge.org/api/v1/%s/search/didyoumean?%s"
# https://dictionary.cambridge.org/api/v1/dictionaries/american-english/topics/topics/the-buttocks/
SAURUS_URL = "https://dictionary.cambridge.org/api/v1/%s/topics/topics/%s/"

API_KEY = None

def spell_check(query, skipSearch=False):
	if not API_KEY:
		raise ConfigException("Require API_KEY for wordsapi. Reload after setting.")
	if not skipSearch and word_search(query):
		return None
	else:
		r = Request(DIDYOUMEAN_URL % (DICT_ORDER[0], urlencode({"q" : query.encode("utf-8")})))
		r.add_header("accessKey", API_KEY)
		return load(urlopen(r))['suggestions']

def word_search(query):
	""" word helper. Returns a dictionary entry."""
	if not API_KEY:
		raise ConfigException("Require API_KEY for wordsapi. Reload after setting.")
	for d in DICT_ORDER:
		r = Request(SEARCH_URL % (d, quote(query.encode("utf-8"))))
		r.add_header("accessKey", API_KEY)
		try:
			f = urlopen(r)
		except HTTPError:
			continue
		data = load(f)
		if 'entryContent' in data:				
			print repr(data['entryContent'])
			data = StringIO(data['entryContent'].encode("utf-8"))
			context = iterparse(data, events=("end","start"))
			# get the root element
			ievent, root = context.next()
			definitions = [] # [[POS, [defs]],]
			usage = None
			defchild = False
			for ievent, elem in context:
				if ievent == "start" and elem.tag == "def":
					defchild = True
				elif ievent == "end" and elem.tag == "pos":
					definitions.append([elem.text, []])
					elem.clear()
				elif ievent == "end" and elem.tag == "def":
					t = elem.text
					if not t:
						t = elem[-1].tail.strip() # get tail (text) of last nested element if there's no main tag text
					if not t: t = "???"
					if usage: 
						t = "(%s) %s" % (usage, t if t[-2] != ":" else t[:-2])
					definitions[-1][-1].append(t)
					usage = None
					defchild = False
					for child in elem: # clear children
						for cchild in child: cchild.clear()
						child.clear()
					elem.clear()
				elif ievent == "end" and elem.tag == "usage":
					usage = elem.text
					elem.clear()
				elif not defchild:
					elem.clear()
			root.clear()
			return definitions
	else:
		return None

def word_synonyms(query):
	if not API_KEY:
		raise ConfigException("Require API_KEY for wordsapi. Reload after setting.")
	
	data = None
	for d in DICT_ORDER:
		r = Request(SEARCH_URL % (d, quote(query.encode("utf-8"))))
		r.add_header("accessKey", API_KEY)
		try:
			f = urlopen(r)
		except HTTPError:
			continue
		data = load(f)
	if not data: return None
	
	topics = data.get("topics", [])
	syns = []
	for t in topics:
		tid = t.get("topicId")
		if tid:
			r = Request(SAURUS_URL % (DICT_ORDER[0], tid))
			r.add_header("accessKey", API_KEY)
			data = load(urlopen(r))	
			for entry in data['entries']:
				syns.append(entry['entryId'])
	return syns
	
def init(bot):
	global API_KEY # oh nooooooooooooooooo
	API_KEY = bot.getOption("API_KEY", module="wordsapi")
	return True

