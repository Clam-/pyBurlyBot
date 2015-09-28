# http://www.wunderground.com/
# require APIkey module option

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from json import load
from traceback import format_exc
from re import compile as recompile

REQUIRES = ("pbm_location", "pbm_wuapi")
WUAPI_MODULE = None
LOC_MODULE = None

# Weather for Lansing, MI: 32.2F (0.1C), Wind Chill of 25F (-4C), Partly Cloudy, Humidity 67%, Wind from the East at 8.0mph (12.9km/h) 
#gusting to 14.0mph (22.5km/h), Low/High 38F/41F (3C/5C).  Flurries or snow showers possible early. A mix of clouds and sun. 
#High 41F. Winds S at 10 to 20 mph.
WEATHER_RPL = "Weather for %s: \x02%sF\x02 (\x02%sC\x02), Low/High \x02%sF\x02/\x02%sF\x02 (\x02%sC\x02/\x02%sC\x02), %s, Humidity %s, %s %s"
WEATHER_RPL_WC = "Weather for %s: \x02%sF\x02 (\x02%sC\x02), Wind Chill of \x02%sF\x02 (\x02%sC\x02), Low/High \x02%sF\x02/\x02%sF\x02 (\x02%sC\x02/\x02%sC\x02), %s, Humidity %s, %s %s"
GHETTOWIND_REGEX = recompile(r'Winds [NSEW]{1,3} at (\d+) to (\d+) (km/h)\.')
GHETTOTEMP_REGEX = recompile(r'\. (?:High|Low) (?:near )?(?:-)?\d+C\.')

# Forecast for Ann Arbor, MI: Today - Chance of Showers 54F/77F (12C/25C), Wed - Clear 55F/81F (13C/27C), Thu - Mostly Sunny 57F/84F (14C/29C), Fri - Mostly Sunny 63F/88F (17C/31C)
FORECAST_RPL = "Forecast for %s: %s"
# Today - Chance of Showers 54F/77F (12C/25C) PoP: %s Hum: %s
FORECAST_DAY = "%s - %s \x02%sF\x02/\x02%sF\x02 (\x02%sC\x02/\x02%sC\x02) PoP: \x02%s%%\x02 Hum: \x02%s%%\x02"
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

def _build_locname(loc):
	l = []
	if loc['city']: l.append(loc['city'])
	if loc['state']: l.append(loc['state'])
	if loc['country_iso3166']: l.append(loc['country_iso3166'])
	return ", ".join(l)

def weather(event, bot):
	""" weather [user/location]. If user/location is not provided, weather is displayed for the requesting nick.
	Otherwise the weather for the requested user/location is displayed."""
	loc = LOC_MODULE.getLocationWithError(bot, event.argument, event.nick)
	if not loc: return
	name, lat, lon = loc
	weather = WUAPI_MODULE.get_weather(lat, lon)
	obs = weather['current_observation']
	fore = weather['forecast']
	outlook = GHETTOWIND_REGEX.sub(_formatWind, fore['txt_forecast']['forecastday'][0]['fcttext_metric'])
	# replace . High 14F. with nothing.
	outlook = GHETTOTEMP_REGEX.sub(".", outlook)
	fore = fore['simpleforecast']['forecastday'][0]
	# build wind
	if obs['wind_kph'] == 0:
		wind = "Calm wind."
	else:
		wind = "Wind from the %s at %s/%s (Gusts of %s/%s) MPH/KPH." % (obs['wind_dir'], obs['wind_mph'], obs['wind_kph'],
			obs['wind_gust_mph'], obs['wind_gust_kph'])
	
	if obs['windchill_string'] == "NA":
		return bot.say(WEATHER_RPL % (_build_locname(obs["display_location"]), obs['temp_f'], obs['temp_c'],
			fore['low']['fahrenheit'], fore['high']['fahrenheit'], fore['low']['celsius'], fore['high']['celsius'], 
			obs['weather'], obs['relative_humidity'], wind, outlook))
	else:
		return bot.say(WEATHER_RPL_WC % (_build_locname(obs["display_location"]), obs['temp_f'], obs['temp_c'], obs['windchill_f'], obs['windchill_c'],
			fore['low']['fahrenheit'], fore['high']['fahrenheit'], fore['low']['celsius'], fore['high']['celsius'],
			obs['weather'], obs['relative_humidity'], wind, outlook))
	
def forecast(event, bot):
	""" forecast [user/location]. If user/location is not provided, weather forecast information is displayed for the requesting nick.
	Otherwise the weather forecast for the requested user/location is displayed."""
	loc = LOC_MODULE.getLocationWithError(bot, event.argument, event.nick)
	if not loc: return
	name, lat, lon = loc
	
	weather = WUAPI_MODULE.get_weather(lat, lon)
	loc = weather['current_observation']["display_location"]
	days = []
	today = True
	# Today - Chance of Showers 54F/77F (12C/25C) PoP: %s Hum: %s
	for data in weather['forecast']['simpleforecast']['forecastday']:
		if today:
			day = "Today"
		else:
			day = data['date']['weekday']
			
		days.append(FORECAST_DAY % (day, data['conditions'], data['low']['fahrenheit'], data['high']['fahrenheit'],
			data['low']['celsius'], data['high']['celsius'], data['pop'], data['avehumidity']))
		
		today = False
	
	return bot.say(FORECAST_RPL % (_build_locname(loc), ", ".join(days)))

def init(bot):
	global WUAPI_MODULE # oh nooooooooooooooooo
	global LOC_MODULE # oh nooooooooooooooooo
	
	WUAPI_MODULE = bot.getModule("pbm_wuapi")
	LOC_MODULE = bot.getModule("pbm_location")
	return True

#mappings to methods
mappings = (Mapping(command="weather", function=weather), Mapping(command="forecast", function=forecast),)
