# GDQ

from util import Mapping
from urllib2 import build_opener
from lxml.html import parse
from json import load

GDQ_URL = "https://gamesdonequick.com/schedule"
TWITCH_API_URL = "https://api.twitch.tv/kraken/channels/gamesdonequick"
RPL = "Current: \x02%s\x02 (%s) Upcoming: {0} \x0f| %s %s"

def agdq(event, bot):
	upcoming = []
	o = build_opener()
	o.addheaders = [('Accept', 'application/vnd.twitchtv.v2+json')]
	f = o.open(TWITCH_API_URL)
	game = "Don't know"
	eta = "?"
	if f.getcode() == 200:
		game = load(f)['game']
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
		found = False
		for gdata in data:
			if found:
				upcoming.append("\x02%s\x02 by %s (%s)" % (gdata[1], gdata[2], gdata[4].lstrip("0:")[:-3]))
			elif gdata[1].lower() == ngame:
				found = True
				eta = gdata[4].lstrip("0:")[:-3]
		# try searching for incorrect name in timetable:
		if not found:
			ngame = ngame.replace(":", "")
			for gdata in data:
				if found:
					upcoming.append("\x02%s\x02 by %s (%s)" % (gdata[1], gdata[2], gdata[4].lstrip("0:")[:-3]))
				elif gdata[1].lower() == ngame:
					found = True
					eta = gdata[4].lstrip("0:")[:-3]
	if not upcoming: upcoming = ["Don't know"]
	bot.say(RPL % (game, eta, "http://www.twitch.tv/gamesdonequick/popout", "https://gamesdonequick.com/schedule"), 
		strins=", ".join(upcoming))

mappings = (Mapping(command=("gdq", "agdq"), function=agdq),)