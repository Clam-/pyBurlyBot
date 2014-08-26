#evalBAD.py

#simple eval module used for debugging.
# you shouldn't enable this

from util import Mapping, commandSplit
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

def doeval(s):
	try:
		exec(s)
		return None
	except Exception as e:
		return "%s : %s" % (type(e).__name__, e.message)

def runeval(event, bot):
	if bot.isadmin():
		r = blockingCallFromThread(reactor, doeval, event.argument)
		if r: bot.say(r)
		else: bot.say("done.")
	else:
		bot.say("No, you.")

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="eval", function=runeval),)
