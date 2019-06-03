# OpenWeather API
# https://openweathermap.org/api
# Requires:
#     API_KEY: https://openweathermap.org/appid
#     Working location module

from urllib2 import urlopen
from json import load
from util.settings import ConfigException

OPTIONS = {
	"API_KEY" : (unicode, "API key for use with Weather Underground services.", u"not_a_key"),
}

# key, features, lat, lon
URL = "https://api.openweathermap.org/data/2.5/%s?appid=%s&lat=%s&lon=%s&units=metric"

API_KEY = None
CSE_ID = None

def get_weather(lat, lon):
	""" helper to ask WU for current weather. Includes forecast also!"""
	if not API_KEY:
		raise ConfigException("Require API_KEY for OpenWeather API. Reload after setting.")
	f = urlopen(URL % ('weather', API_KEY, lat, lon))
	weather_data = load(f)
	if f.getcode() == 200:
		return weather_data
	else:
		raise RuntimeError("Error (%s): %s" % (f.getcode(), weather_data.replace("\n", " ")))


# Not used for weather because doesn't contain "display_location"
def get_forecast(lat, lon):
	""" helper to ask WU for forecasted weather."""
	if not API_KEY:
		raise ConfigException("Require API_KEY for OpenWeather API. Reload after setting.")
	f = urlopen(URL % ('forecast', API_KEY, lat, lon))
	forecast = load(f)
	if f.getcode() == 200:
		return forecast
	else:
		raise RuntimeError("Error (%s): %s" % (f.getcode(), forecast.replace("\n", " ")))

def init(bot):
	global API_KEY # oh nooooooooooooooooo
	API_KEY = bot.getOption("API_KEY", module="pbm_openweathermap_api")
	return True
