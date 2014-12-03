
# Google services
# require APIkey module option

# TODO: maybe implement some of these neat filters:
# https://developers.google.com/custom-search/json-api/v1/reference/cse/list#request

from urllib2 import Request, urlopen
from urllib import urlencode
from json import load
		
OPTIONS = {
	"API_KEY" : (unicode, "API key for use with Google services.", u"not_a_key"),
	"CSE_ID" : (unicode, "ID of Custom Search Engine to use with Google search.", u"not_an_ID"),
}

URL = "https://www.googleapis.com/customsearch/v1?%s"
LOC_URL = "https://maps.googleapis.com/maps/api/geocode/json?%s"
TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json?%s"
API_KEY = None
CSE_ID = None

def google(query, num_results=1):
	""" google helper. Will return Google search results using the provided query up to num_results results."""
	d = { "q" : query.encode("utf-8"), "key" : API_KEY, "cx" : CSE_ID, "num" : num_results,
		"fields" : "spelling/correctedQuery,items(title,link,snippet)" }
		
	f = urlopen(URL % (urlencode(d)))
	gdata = load(f)
	if f.getcode() == 200:
		results = []
		spelling =  gdata.get("spelling")
		if spelling: spelling = spelling["correctedQuery"]
		if "items" in gdata:
			for item in gdata["items"]:
				snippet = item["snippet"].replace(" \n", " ")
				results.append((item["title"], snippet, item["link"]))
		return (spelling, results)
	else:
		raise RuntimeError("Error: %s" % (gdata.replace("\n", " ")))

def google_image(query, num_results):
	""" google image search helper. Will return Google images using the provided query up to num_results results."""
	d = { "q" : query.encode("utf-8"), "key" : API_KEY, "cx" : CSE_ID, "num" : num_results, "searchType" : "image",
		"fields" : "spelling/correctedQuery,items(title,link)"}
		#TODO: consider displaying img stats like file size and resolution?
	f = urlopen(URL % (urlencode(d)))
	gdata = load(f)
	if f.getcode() == 200:
		results = []
		spelling =  gdata.get("spelling")
		if spelling: spelling = spelling["correctedQuery"]
		if "items" in gdata:
			for item in gdata["items"]:
				results.append((item['title'], item['link']))
		return (spelling, results)
	else:
		raise RuntimeError("Error: %s" % (gdata.replace("\n", " ")))
		
def google_timezone(lat, lon, t):
	""" helper to ask google for timezone information about a location."""
	d = { "location" : "%s,%s" % (lat, lon), "key" : API_KEY, "timestamp" : int(t) }
	f = urlopen(TIMEZONE_URL % (urlencode(d)))
	gdata = load(f)
	if f.getcode() == 200:
		return gdata["timeZoneId"], gdata["timeZoneName"], gdata["dstOffset"], gdata["rawOffset"]
	else:
		raise RuntimeError("Error (%s): %s" % (f.getcode(), gdata.replace("\n", " ")))
		
def google_geocode(query):
	""" helper to ask google for location data. Returns name, lat, lon"""
	d = {"address" : query.encode("utf-8"), "key" : API_KEY }
	f = urlopen(LOC_URL % (urlencode(d)))
	locdata = load(f)
	if f.getcode() == 200:
		if "results" in locdata:
			item = locdata["results"]
			if len(item) == 0:
				return None
			item = locdata["results"][0]
			ll = item.get("geometry", {}).get("location") # lol tricky
			if not ll: return None
			return item["formatted_address"], ll["lat"], ll["lng"]
		else:
			return None
	else:
		raise RuntimeError("Error (%s): %s" % (f.getcode(), locdata.replace("\n", " ")))

def init(bot):
	global API_KEY # oh nooooooooooooooooo
	global CSE_ID # oh nooooooooooooooooo
	API_KEY = bot.getOption("API_KEY", module="google")
	CSE_ID = bot.getOption("CSE_ID", module="google")
	return True

