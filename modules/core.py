#core internal BurlyBot commands
# things like .reload
from util import Mapping
from util.settings import Settings

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
###

def reloadmods(event, bot):
	if bot.isadmin():
		#reload settings, important to do only from within reactor
		reactor.callFromThread(Settings.reload)
		#also refresh dispatchers
		blockingCallFromThread(reactor, Settings.reloadDispatchers)
		bot.say("Done.")
	else:
		bot.say("No, you.")
	return

mappings = (Mapping(types=["privmsged"], command="reload", function=reloadmods),)
