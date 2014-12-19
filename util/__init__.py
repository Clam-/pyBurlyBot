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

def pastehelper(bot, basemsg, items=None, altmsg=None, sep=(", ","\n"), force=False, **kwargs):
	""" If using items, altmsg is an alternate basestring to use for interpolation with the items list."""
	tmsg = basemsg
	if not force:
		if items is not None:
			tmsg = basemsg % sep[0].join(items)
		if bot.checkSay(tmsg):
			return bot.say(tmsg)
	try:
		if items is not None:
			if altmsg: url = ADDONS.paste(altmsg % sep[1].join(items), **kwargs)
			else: url = ADDONS.paste(basemsg % sep[1].join(items), **kwargs)
		else:
			url = ADDONS.paste(basemsg, **kwargs)
		if url:
			bot.say(basemsg % url)
		else:
			bot.say(basemsg % "Error: paste addon failure.")
	except AttributeError:
		if items is not None:
			bot.say(basemsg % "Error: too many entries to list and no paste addon.")
		else:
			bot.say(basemsg % "Error: too much data and no paste addon.")
				
def englishlist(l):
	if len(l) > 1: return "%s and %s" % (", ".join(l[:-1]), l[-1])
	else: return l[0]
