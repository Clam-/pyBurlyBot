#debugging.py

#some commands to facilitate debugging

from util import Mapping, TimeoutException
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

def flood(event, bot):
	for x in xrange(7):
		bot.say("Hello %s" % x)

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="flood", function=flood),
	)
