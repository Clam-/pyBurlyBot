#debugging.py

#some commands to facilitate debugging
# you shouldn't enable this

from util import Mapping, TimeoutException, commandSplit
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

def doeval(bot, event):
	try:
		exec(event.argument)
		return None
	except Exception as e:
		return "%s : %s" % (type(e).__name__, e.message)

# WARNING: DO NOT CALL A METHOD THAT CALLS "blockingCallFromThread", you will have bad time and freeze bot.
def runeval(event, bot):
	if bot.isadmin():
		r = blockingCallFromThread(reactor, doeval, bot, event)
		if r: bot.say(r)
		else: bot.say("done.")
	else:
		bot.say("No, you.")

def flood(event, bot):
	for x in xrange(7):
		bot.say("Hello %s" % x)

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="eval", function=runeval),
	Mapping(types=["privmsged"], command="flood", function=flood),)
