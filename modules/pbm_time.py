# time module

from util import Mapping
from time import gmtime, strftime
from calendar import timegm # silly python... I just want UTC seconds

# You could do this without web based service but whatever, offloading is easier. Cloud7.0
REQUIRES = ("pbm_location", "pbm_googleapi", "pbm_users")
LOC_MODULE = None
GAPI_MODULE = None
USERS_MODULE = None

def ttime(event, bot):
	# lookup location offset
	# apply to : timegm(gmtime())
	loc = LOC_MODULE.getLocationWithError(bot, event.argument, event.nick)
	if not loc: return
	name, lat, lon = loc
	t = timegm(gmtime())
	tz = GAPI_MODULE.google_timezone(lat, lon, t)
	if not tz: return bot.say("Can't find timezone information for (%s, %s, %s)" % (name, lat, lon))
	# gdata["timeZoneId"], gdata["timeZoneName"], gdata["dstOffset"], gdata["rawOffset"]
	t = t + tz[2] + tz[3]
	#TODO: what time format??
	bot.say("%s - %s (%s-%s)" % (strftime("%c", gmtime(t)), name, tz[0], tz[1]))
		
def init(bot):
	global LOC_MODULE # oh nooooooooooooooooo
	global GAPI_MODULE # oh nooooooooooooooooo
	global USERS_MODULE # oh nooooooooooooooooo
	
	# cache user module.
	# NOTE: you should only call getModule in init() if you have preloaded it first using "REQUIRES"
	LOC_MODULE = bot.getModule("pbm_location")
	GAPI_MODULE = bot.getModule("pbm_googleapi")
	USERS_MODULE = bot.getModule("pbm_users")
	return True
	
mappings = (Mapping(command=("time","t"), function=ttime),)
