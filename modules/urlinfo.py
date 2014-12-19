# urlinfo module

# Using Requests because easier

from util import Mapping, commandSplit, functionHelp, fetchone
from re import compile as recompile

from requests import head

from time import strftime, strptime

# (code - reason) content-type, encoding, size, serversoftware, redirect
HEAD_RPL = "(%s - %s) %s, %s%s bytes, %s%s"

def seen_link(event, bot):
	match = event.regex_match
	pos = match.regs[0]
	url = match.string[pos[0]:pos[1]]
	print url, match
	bot.dbQuery("""INSERT OR REPLACE INTO urlinfo (source, url) 
		VALUES (?,?);""", (event.target, url))

def headers(event, bot):
	""" head [URL]. If no argument is provided the headers of the last URL will be displayed. 
	Otherwise the title of the provided URL will be displayed."""
	if not event.argument:
		row = bot.dbQuery("""SELECT url FROM urlinfo 
								WHERE source=?;""", (event.target,), fetchone)
		if not row:
			return bot.say("Haven't seen any URLs in here.")
		url = row['url']
	else:
		url = event.argument
	
	resp = head(url)
	h = resp.headers
	ctype = h.get("content-type", "?;").split(";")[0]
	server = h.get("server", "?")
	size = int(h.get("content-length", 0))
	if "location" in h: location = " -> %s" % h["location"]
	else: location = ""
	encoding = "%s, " % resp.encoding if resp.encoding else ""
	bot.say(HEAD_RPL % (resp.status_code, resp.reason, ctype, encoding, size, server, location) )

def title(event, bot):
	""" title [URL]. If no argument is provided the title of the last URL will be displayed. 
	Otherwise the title of the provided URL will be displayed."""
	if not event.argument: 
		return show_youtube_info(event, bot)
	if GAPI_MODULE.google_youtube_check(event.argument):
		return show_youtube_info(event, bot)
	numresults, results = GAPI_MODULE.google_youtube_search(event.argument)
	if results:
		lr = len(results)
		rpl = ", ".join([RESULT_TEXT] * lr)
		links = []
		titles = []
		for item in results:
			id = item['id']
			if id['kind'] == 'youtube#video':
				links.append(SHORTURL % item['id']['videoId'])
			elif id['kind'] == 'youtube#channel':
				links.append(CHANNELURL % item['id']['channelId'])
			titles.append(item['snippet']['title'])
		rpl = (rpl % tuple(xrange(lr))) % tuple(links)
		
		bot.say(rpl, fcfs=False, strins=titles)
	else:
		bot.say("(%s) No results found." % numresults)

def init(bot):
	global GAPI_MODULE # oh nooooooooooooooooo
	
	bot.dbCheckCreateTable("urlinfo", 
		'''CREATE TABLE urlinfo(
			source TEXT PRIMARY KEY COLLATE NOCASE,
			url TEXT
		);''')
	GAPI_MODULE = bot.getModule("googleapi")
	return True

#mappings to methods
mappings = (Mapping(command=("head"), function=headers), Mapping(command=("title"), function=title),
	Mapping(types=["privmsged"], regex=recompile(r"\bhttp(s)?\://.+(/)?\b"), function=seen_link),)
