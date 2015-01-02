# time module

from util import Mapping
from time import gmtime, strftime
from calendar import timegm # silly python... I just want UTC seconds

# for google API key, could do without the google requirement if we just
# .getOption(module="google"), but would seem kind of strange

# You could do this without web based service but whatever, offloading is easier. Cloud7.0
REQUIRES = ("location", "googleapi", "users")
LOC_MODULE = None
GAPI_MODULE = None
USERS_MODULE = None

def ttime(event, bot):
	# lookup location offset
	# apply to : timegm(gmtime())
	# TODO: SHARED CODE between time.py and weather.py
	target = event.argument
	user = None
	isself = False
	if target: 
		user = USERS_MODULE.get_username(bot, target, event.nick)
		if user == USERS_MODULE.get_username(bot, event.nick): isself = True
	else:
		user = USERS_MODULE.get_username(bot, event.nick)
		target = user
	if user:
		#get location
		loc = LOC_MODULE.getlocation(bot.dbQuery, user)
		if not loc: 
			if isself: return bot.say("Your location isn't known. Try using location." % target)
			else: return bot.say("Location not known for (%s). Try getting them to set it." % target)
	else:
		# lookup location
		loc = LOC_MODULE.lookup_location(target)
		if not loc: return bot.say("I don't know where (%s) is." % target)
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
	LOC_MODULE = bot.getModule("location")
	GAPI_MODULE = bot.getModule("googleapi")
	USERS_MODULE = bot.getModule("users")
	return True
	
mappings = (Mapping(command=("time","t"), function=ttime),)
