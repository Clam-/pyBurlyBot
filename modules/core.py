#core internal BBM commands
# things like .reload
from util import Mapping, Settings
from util.dispatcher import Dispatcher

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
###

def reloadmods(event, botinst):
	#should probably check for some kind of admin shits or something... How to get BBM Global settings.
	# I vote "settings" should be in another module, so can just import it, lol.
	if botinst.isadmin("core"):
		#reload settings first, then dispatcher
		Settings.reload()
		#let's send this method to the reactor thread ONLY MODIFY DISPATCHER IN REACTOR THREAD PLEASE.
		reactor.callFromThread(Dispatcher.reload)
		botinst.msg(event.channel, "Done.")
	else:
		botinst.msg(event.channel, "Nou.")
	return

def init():
	return True

mappings = (Mapping(types=["privmsg"], command="reload", function=reloadmods),)
