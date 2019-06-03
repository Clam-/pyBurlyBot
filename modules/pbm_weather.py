# http://www.wunderground.com/
# require APIkey module option

from util import Mapping, commandSplit, functionHelp
from urllib2 import Request, urlopen, HTTPError
from urllib import urlencode
from json import load
from traceback import format_exc
from re import compile as recompile

REQUIRES = ("pbm_location", "pbm_openweathermap_api")
OWNAPI_MODULE = None
LOC_MODULE = None

# Weather for Lansing, MI: 32.2F (0.1C), Wind Chill of 25F (-4C), Partly Cloudy, Humidity 67%, Wind from the East at 8.0mph (12.9km/h) 
#gusting to 14.0mph (22.5km/h), Low/High 38F/41F (3C/5C).  Flurries or snow showers possible early. A mix of clouds and sun. 
#High 41F. Winds S at 10 to 20 mph.
WEATHER_RPL = "Weather for %s: \x02%.1fF\x02 (\x02%.1fC\x02), Low/High \x02%.1fF\x02/\x02%.1fF\x02 (\x02%.1fC\x02/\x02%.1fC\x02), %s, Humidity %s%%, %s"
WEATHER_RPL_WC = "Weather for %s: \x02%.1fF\x02 (\x02%.1fC\x02), Wind Chill of \x02%.1fF\x02 (\x02%.1fC\x02), Low/High \x02%.1fF\x02/\x02%.1fF\x02 (\x02%.1fC\x02/\x02%.1fC\x02), %s, Humidity %s%%, %s"
# Forecast for Ann Arbor, MI: Today - Chance of Showers 54F/77F (12C/25C), Wed - Clear 55F/81F (13C/27C), Thu - Mostly Sunny 57F/84F (14C/29C), Fri - Mostly Sunny 63F/88F (17C/31C)
FORECAST_RPL = "Forecast for %s: %s"
# Today - Chance of Showers 54F/77F (12C/25C) PoP: %s Hum: %s
FORECAST_DAY = "%s - %s \x02%sF\x02/\x02%sF\x02 (\x02%sC\x02/\x02%sC\x02) PoP: \x02%s%%\x02 Hum: \x02%s%%\x02"

def c2f(temp_c):
	return (temp_c * 1.8) + 32.0

def f2c(temp_f):
	return (temp_f - 32) * (5.0/9.0)

def kph2mph(kph):
	return kph / 1.6093440

def degrees_to_cardinal(d):
	"""
	This is an approximation
	"""
	dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
			"S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
	ix = int((d + 11.25)/22.5)
	return dirs[ix % 16]


def wind_chill(temp_c, wind_speed):
	""" Compute wind chill given temperature and wind speed if the
		temperature is 50 degrees Fahrenheit or less and the wind speed is
		above 3 mph, otherwise return 'nan' (not-a-number) because it's an
		undefined quantity in those situations.
	"""
	temp_f = c2f(temp_c)
	wind_speed = kph2mph(wind_speed)
	if temp_f <= 50 and wind_speed > 3:
		windchill = (35.74 + (0.6215 * temp_f) - 35.75 * (wind_speed ** 0.16)
				+ 0.4275 * temp_f * (wind_speed ** 0.16))
		# Not sure on this, we'll try it out
		if abs(temp_f - windchill) >= 3.0:
			return f2c(windchill)
	return None


def _build_locname(place, cc):
	return '%s, %s' % (place, cc)


def weather(event, bot):
	""" weather [user/location]. If user/location is not provided, weather is displayed for the requesting nick.
	Otherwise the weather for the requested user/location is displayed."""
	loc = LOC_MODULE.getLocationWithError(bot, event.argument, event.nick)
	if not loc: return
	name, lat, lon = loc
	weather = OWNAPI_MODULE.get_weather(lat, lon)
	place_name = weather['name']
	country_code = weather['sys']['country']
	temp_c = weather['main']['temp']
	temp_max_c = weather['main']['temp_max']
	temp_min_c = weather['main']['temp_min']
	humidity = weather['main']['humidity']
	wind_kph = weather['wind']['speed']
	wind_cardinal = degrees_to_cardinal(weather['wind']['deg'])
	simple_conditions = weather['weather'][0]['main']
	windchill_c = wind_chill(temp_c, wind_kph)
	if wind_kph <= 4:
		wind = 'Calm wind.'
	else:
		wind = "Wind from the %s at %.1f/%.1f MPH/KPH." % (wind_cardinal, kph2mph(wind_kph), wind_kph)
	if windchill_c:
		bot.say(WEATHER_RPL_WC % (_build_locname(place_name, country_code), c2f(temp_c), temp_c, c2f(windchill_c), windchill_c,
			c2f(temp_min_c), c2f(temp_max_c), temp_min_c, temp_max_c, simple_conditions, humidity, wind))
	else:
		bot.say(WEATHER_RPL % (_build_locname(place_name, country_code), c2f(temp_c), temp_c,
			c2f(temp_min_c), c2f(temp_max_c), temp_min_c, temp_max_c, simple_conditions, humidity, wind))

	
def forecast(event, bot):
	""" forecast [user/location]. If user/location is not provided, weather forecast information is displayed for the requesting nick.
	Otherwise the weather forecast for the requested user/location is displayed."""
	return bot.say('coming soon')
	loc = LOC_MODULE.getLocationWithError(bot, event.argument, event.nick)
	if not loc: return
	name, lat, lon = loc
	
	weather = OWNAPI_MODULE.get_weather(lat, lon)
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
	global OWNAPI_MODULE # oh nooooooooooooooooo
	global LOC_MODULE # oh nooooooooooooooooo
	
	OWNAPI_MODULE = bot.getModule("pbm_openweathermap_api")
	LOC_MODULE = bot.getModule("pbm_location")
	return True

#mappings to methods
mappings = (Mapping(command="weather", function=weather), Mapping(command="forecast", function=forecast),)
