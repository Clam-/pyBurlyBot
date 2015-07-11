# reload module

from util import Mapping

### Modules should not import this! Unless they have a very good reason to.
from util.settings import Settings

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
###

def _reallyReload():
	Settings.reloadStage1()
	Settings.reloadStage2()
	
def reloadbot(event, bot):
	if bot.isadmin():
		#reload settings, important to do only from within reactor
		#also refresh dispatchers
		blockingCallFromThread(reactor, _reallyReload)
		# may never get sent if bot is disconnecting from this server after reload
		bot.say("Done.")
	else:
		bot.say("No, you.")
	return
	
mappings = (Mapping(command="reload", function=reloadbot),)

