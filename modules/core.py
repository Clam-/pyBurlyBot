#core internal BBM commands
# things like .reload
from util import Mapping, Settings
from util.dispatcher import Dispatcher

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
###

def reloadmods(event, botinst):
	if botinst.isadmin("core"):
		#reload settings first, then dispatcher
		# let's only modify Settings in reactor as well
		reactor.callFromThread(Settings.reload)
		# let's send this method to the reactor thread ONLY MODIFY DISPATCHER IN REACTOR THREAD PLEASE.
		reactor.callFromThread(Dispatcher.reload)
		botinst.msg(event.channel, "Done.")
	else:
		botinst.msg(event.channel, "Nou.")
	return

def init():
	return True

mappings = (Mapping(types=["privmsged"], command="reload", function=reloadmods),)
