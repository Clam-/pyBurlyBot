# GDQ

from util import Mapping
from urllib2 import build_opener
from lxml.html import parse
from json import load
from time import gmtime, strptime
from calendar import timegm # silly python... I just want UTC seconds

OPTIONS = {
	"TWITCH_CLIENTID" : (unicode, "Client ID for use in Twitch API calls.", u""),
}

GDQ_URL = "https://gamesdonequick.com/schedule"
TWITCH_API_URL = "https://api.twitch.tv/kraken/channels/gamesdonequick"
RPL = "Current: \x02%s\x02 (%s) Upcoming: {0} \x0f| %s %s"
TWITCH_CLIENTID = None

def _searchGame(data, title):
	# try searching for incorrect name in timetable take 3:
	found = False
	upcoming = []
	eta = None
	for gdata in data:
		# ignore silly entires:
		if len(gdata) < 4: continue
		if found:
			# fix for mid 2016 in gdata[3]
			upcoming.append("\x02%s\x02 by %s (%s)" % (gdata[1], gdata[2], gdata[3].strip().lstrip("0:")[:-3]))
		elif gdata[1].lower() == title:
			found = True
			eta = gdata[3].strip()
	return upcoming, eta

def modifyNameIter(gamename):
	yield gamename
	if ":" in gamename:
		for x in (gamename.replace(":", ""), gamename.split(":")[0]):
			yield x
		if "two" in gamename: yield gamename.replace(":", "").replace("two", "2")
	if u"\u2013" in gamename:
		yield gamename.split(u"\u2013")[0].strip()
	if "two" in gamename:
		yield gamename.replace("two", "2")
	if "!" in gamename:
		yield gamename.rstrip("!")
	if "the" in gamename:
		yield gamename.replace("the ", "")

def gdq(event, bot):
	upcoming = []
	o = build_opener()
	o.addheaders = [('Client-ID', TWITCH_CLIENTID)]
	f = o.open(TWITCH_API_URL)
	game = "Don't know"
	eta = None
	if f.getcode() == 200:
		data = load(f)
		game = data['game']
		gstart = timegm(strptime(data['updated_at'], "%Y-%m-%dT%H:%M:%SZ")) #"2015-01-06T01:11:32Z" UTC
		ngame = game.lower()
		o = build_opener()
		o.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')]
		f = o.open(GDQ_URL)
		# http://stackoverflow.com/a/9920703
		page = parse(f)
		rows = page.xpath("body/div//table/tbody")[0].findall("tr")
		
		data = []
		for row in rows:
			data.append([c.text_content() for c in row.getchildren()])
		# find current
		upcoming = None
		# try searching for incorrect name in timetable because bads...
		for igametitle in modifyNameIter(ngame):
			upcoming, eta = _searchGame(data, igametitle)
			if upcoming: break
		else:
			if ngame[:4] == "the ":
				upcoming, eta = _searchGame(data, ngame[4:])
		
		if eta:
			curr = timegm(gmtime())
			neta = timegm(strptime(eta, "%H:%M:%S")) - timegm(strptime("0:00:00", "%H:%M:%S"))
			eta = "%s/%s" % (eta.lstrip("0:")[:-3], (neta - (curr-gstart))/60)
		else: eta = "?"
	if not upcoming: upcoming = ["Don't know"]
	bot.say(RPL % (game, eta, "http://www.twitch.tv/gamesdonequick/popout", "https://gamesdonequick.com/schedule"), 
		strins=", ".join(upcoming))


def init(bot):
	global TWITCH_CLIENTID # oh nooooooooooooooooo
	TWITCH_CLIENTID = bot.getOption("TWITCH_CLIENTID", module="pbm_gdq")
	return True

mappings = (Mapping(command=("gdq", "agdq", "sgdq"), function=gdq),)
