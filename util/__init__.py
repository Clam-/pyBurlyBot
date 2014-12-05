# utils for modules to import
from timer import Timers
from container import TimeoutException
from helpers import distance_of_time_in_words, processHostmask, commandSplit, argumentSplit, commandlength, functionHelp

from mapping import Mapping

from db import fetchone, fetchall, fetchmany

# Access to addons is not currently managed through the reactor, so if a module requests an addon
# while bot is reloading, potential threaded problem may arise. I don't really want to bog down addon
# access by going through the reactor.
# TODO: This currently doesn't respect allowed/deny modules. Once a provider is loaded it's available for all.
# 		Again, if we change this, we need to access settings, and then slowed down by reactor. On the plus side
#		if we reactor for that reason, then we get thread sanity, probably.
#		And then Addons might as well be part of the container... like dispatcher.
class _ADDONS(object):
	def __init__(self):
		self._dict = {}
	
	def clear(self):
		self._dict.clear()
		
	def _add(self, name, f):
		self._dict[name] = f
		
	def __getattr__(self, attr):
		try:
			return self._dict[attr]
		except KeyError:
			raise AttributeError("No provider for %s" % attr)
		
ADDONS = _ADDONS()

def pastehelper(bot, basemsg, items=None, sep=(", ","\n"), **kwargs):
	tmsg = basemsg
	if items:
		tmsg = basemsg % sep[0].join(items)
	if bot.checkSay(tmsg):
		bot.say(tmsg)
	else:
		try:
			if items:
				url = ADDONS.paste(basemsg % sep[1].join(items), **kwargs)
			else:
				url = ADDONS.paste(basemsg, **kwargs)
			if url:
				bot.say(basemsg % url)
			else:
				bot.say(basemsg % "Error: paste addon failure.")
		except AttributeError:
			if items:
				bot.say(basemsg % "Error: too many entries to list and no paste addon.")
			else:
				bot.say(basemsg % "Error: too much data and no paste addon.")
				
def stringlist(l):
	if len(l) > 1: return "%s and %s" % (", ".join(l[:-1]), l[-1])
	else: return l[0]
