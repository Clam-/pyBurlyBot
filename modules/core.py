#core internal BBM commands
# things like .reload
from util import Mapping, Settings
from util.dispatcher import Dispatcher

def reloadmods(event, botinst):
	#should probably check for some kind of admin shits or something... How to get BBM Global settings.
	# I vote "settings" should be in another module, so can just import it, lol.
	if event.nick in Settings.getModuleOption("core", "admins", botinst.network):
		#reload settings first, then dispatcher
		Settings.reload()
		Dispatcher.reload() #lol will this even work
		botinst.msg(event.channel, "Done.")
	else:
		botinst.msg(event.channel, "Nou.")
	return

def init():
	return True

mappings = (Mapping(types=["privmsg"], command="reload", function=reloadmods),)
