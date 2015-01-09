# GDQ

from util import Mapping
from urllib2 import build_opener
from lxml.html import parse
from json import load
from time import gmtime, strptime
from calendar import timegm # silly python... I just want UTC seconds

GDQ_URL = "https://gamesdonequick.com/schedule"
TWITCH_API_URL = "https://api.twitch.tv/kraken/channels/gamesdonequick"
RPL = "Current: \x02%s\x02 (%s) Upcoming: {0} \x0f| %s %s"

def _searchGame(data, title):
	# try searching for incorrect name in timetable take 3:
	found = False
	upcoming = []
	eta = None
	for gdata in data:
		if found:
			upcoming.append("\x02%s\x02 by %s (%s)" % (gdata[1], gdata[2], gdata[4].lstrip("0:")[:-3]))
		elif gdata[1].lower() == title:
			found = True
			eta = gdata[4]
	return upcoming, eta

def agdq(event, bot):
	upcoming = []
	o = build_opener()
	o.addheaders = [('Accept', 'application/vnd.twitchtv.v2+json')]
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
		rows = page.xpath("body/table/tbody")[0].findall("tr")
		data = []
		for row in rows:
			data.append([c.text for c in row.getchildren()])
		# find current
		upcoming = None
		
		# try searching for incorrect name in timetable because bads...
		for igametitle in (ngame, ngame.replace(":", ""), ngame.split(":")[0], ngame.split(u"\u2013")[0].strip(), 
				ngame.replace("two", "2"), ngame.replace(":", "").replace("two", "2")):
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

mappings = (Mapping(command=("gdq", "agdq"), function=agdq),)