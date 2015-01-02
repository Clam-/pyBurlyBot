# http://www.wunderground.com/
# require APIkey module option

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from json import load
from traceback import format_exc
from re import compile as recompile

REQUIRES = ("location", "wuapi", "users")
WUAPI_MODULE = None
LOC_MODULE = None
USERS_MODULE = None

# Weather for Lansing, MI: 32.2F (0.1C), Wind Chill of 25F (-4C), Partly Cloudy, Humidity 67%, Wind from the East at 8.0mph (12.9km/h) 
#gusting to 14.0mph (22.5km/h), Low/High 38F/41F (3C/5C).  Flurries or snow showers possible early. A mix of clouds and sun. 
#High 41F. Winds S at 10 to 20 mph.

WEATHER_RPL = "Weather for %s, %s, %s: \x02%sF\x02 (\x02%sC\x02), Low/High \x02%sF\x02/\x02%sF\x02 (\x02%sC\x02/\x02%sC\x02), %s, Humidity %s, %s %s"
WEATHER_RPL_WC = "Weather for %s, %s, %s: %s Low/High %s, Wind Chill of %s, Humidity %s, %s %s"
GHETTOWIND_REGEX = recompile(r'Winds [NSEW]{1,3} at (\d+) to (\d+) (mph)\.')
GHETTOTEMP_REGEX = recompile(r'\. (?:High|Low) (?:near )?(?:-)?\d+\. ')

def _formatWind(matchobj):
	mpos = matchobj.regs
	orig = matchobj.string
	# e.g. ((61, 85), (72, 74), (78, 80), (81, 84))
	#        whole,    speed1,    speed2,  unit
	pre = orig[mpos[0][0]:mpos[1][0]]
	
	speed1 = int(float(matchobj.group(1))) # int(float( to make sure
	speed1 = "%s/%s" % (speed1, int(round(speed1*1.609344)))
	
	speed2 = int(float(matchobj.group(2))) # int(float( to make sure
	speed2 = "%s/%s" % (speed2, int(round(speed2*1.609344)))
	
	return "%s%s%s%s %s" % (pre, speed1, orig[mpos[1][1]:mpos[2][0]], speed2, "MPH/KPH")

def weather(event, bot):
	""" weather [user/location]. If user/location is not provided, weather is displayed for the requesting nick.
	Otherwise the weather for the requested user/location is displayed."""
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
	weather = WUAPI_MODULE.get_weather(lat, lon)
	obs = weather['current_observation']
	fore = weather['forecast']

	outlook = GHETTOWIND_REGEX.sub(_formatWind, fore['txt_forecast']['forecastday'][0]['fcttext'])
	# replace . High 14F. with nothing.
	outlook = GHETTOTEMP_REGEX.sub("\. ", outlook)
	fore = fore['simpleforecast']['forecastday'][0]
	loc = obs["display_location"]
	# build wind
	if obs['wind_kph'] == 0:
		wind = "Calm wind."
	else:
		wind = "Wind from the %s at %s/%s (Gusts of %s/%s MPH/KPH.)" % (obs['wind_dir'], obs['wind_mph'], obs['wind_kph'],
			obs['wind_gust_mph'], obs['wind_gust_kph'])
	
	if obs['windchill_string'] != "NA":
		return bot.say(WEATHER_RPL % (loc['city'], loc['state'], loc['country_iso3166'], obs['temp_f'], obs['temp_c'],
			fore['low']['fahrenheit'], fore['high']['fahrenheit'], fore['low']['celsius'], fore['high']['celsius'], 
			obs['weather'], obs['relative_humidity'], wind, outlook))
	else:
		return bot.say(WEATHER_RPL_WC % (loc['city'], loc['state'], loc['country_iso3166'], obs['temperature_string'], 
			fore['low']['fahrenheit'], fore['high']['fahrenheit'], fore['low']['celsius'], fore['high']['celsius'],
			obs['windchill_string'], obs['weather'], obs['relative_humidity'], wind, outlook))
	
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
	return bot.say("Tell Griff to fix me. Forecast: %s" % forecast)

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
