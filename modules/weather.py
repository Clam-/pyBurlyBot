# http://www.wunderground.com/
# require APIkey module option

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from json import load

from traceback import format_exc

REQUIRES = ("location", "wuapi", "users")
WUAPI_MODULE = None
LOC_MODULE = None
USERS_MODULE = None

# Weather for Lansing, MI: 32.2F (0.1C), Wind Chill of 25F (-4C), Partly Cloudy, Humidity 67%, Wind from the East at 8.0mph (12.9km/h) 
#gusting to 14.0mph (22.5km/h), Low/High 38F/41F (3C/5C).  Flurries or snow showers possible early. A mix of clouds and sun. 
#High 41F. Winds S at 10 to 20 mph.
def weather(event, bot):
	""" weather [user/location]. If user/location is not provided, weather is displayed for the requesting nick.
	Otherwise the weather for the requested user/location is displayed."""
	#copy paste from time.py
	target = event.argument
	user = None
	if target: 
		user = USERS_MODULE.get_username(bot, target, event.nick)
	else:
		user = USERS_MODULE.get_username(bot, event.nick)
		target = user
	if user:
		#get location
		loc = LOC_MODULE.getlocation(bot.dbQuery, user)
		if not loc: return bot.say("Location not known for (%s), try using location" % target)
	else:
		# lookup location
		loc = LOC_MODULE.lookup_location(target)
		if not loc: return bot.say("I don't know where (%s) is." % target)
	name, lat, lon = loc
	weather = WUAPI_MODULE.get_weather(lat, lon)
	return bot.say("Weather: %s" % weather)
	
def forecast(event, bot):
	""" forecast [user/location]. If user/location is not provided, weather forecast information is displayed for the requesting nick.
	Otherwise the weather forecast for the requested user/location is displayed."""
	#copy paste from time.py
	target = event.argument
	user = None
	if target: 
		user = USERS_MODULE.get_username(bot, target, event.nick)
	else:
		user = USERS_MODULE.get_username(bot, event.nick)
		target = user
	if user:
		#get location
		loc = LOC_MODULE.getlocation(bot.dbQuery, user)
		if not loc: return bot.say("Location not known for (%s), try using location" % target)
	else:
		# lookup location
		loc = LOC_MODULE.lookup_location(target)
		if not loc: return bot.say("I don't know where (%s) is." % target)
	name, lat, lon = loc
	
	forecast = WUAPI_MODULE.get_forecast(lat, lon)
	return bot.say("Forecast: %s" % forecast)

def init(bot):
	global WUAPI_MODULE # oh nooooooooooooooooo
	global LOC_MODULE # oh nooooooooooooooooo
	global USERS_MODULE # oh nooooooooooooooooo
	
	WUAPI_MODULE = bot.getModule("wuapi")
	LOC_MODULE = bot.getModule("location")
	USERS_MODULE = bot.getModule("users")
	return True

#mappings to methods
mappings = (Mapping(command=("weather"), function=weather),)
