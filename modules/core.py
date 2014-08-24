#core internal BurlyBot commands
# things like .reload
from util import Mapping
from util.dispatcher import Dispatcher
from util.settings import Settings

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
###

def reloadmods(event, bot):
	if bot.isadmin():
		#reload settings, important to do only from within reactor
		reactor.callFromThread(Settings.reload)
		#also refresh dispatchers
		reactor.callFromThread(Settings.reloadDispatchers)
		bot.msg(event.channel, "Done.")
	else:
		bot.msg(event.channel, "No, you.")
	return

mappings = (Mapping(types=["privmsged"], command="reload", function=reloadmods),)
