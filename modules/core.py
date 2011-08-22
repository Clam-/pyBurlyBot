from util import Mapping
#core internal BBM commands
# things like .reload
from settings import Settings

def reloadmods(event, botinst, db):
	#should probably check for some kind of admin shits or something... How to get BBM Global settings.
	# I vote "settings" should be in another module, so can just import it, lol.
	if event.nick in Settings.getModuleOption("core", "admins", botinst.servername):
		#reload settings first, then dispatcher
		Settings.reload()
		Settings.dispatcher.reload() #lol will this even work
		botinst.msg(event.channel, "Done.")
	else:
		botinst.msg(event.channel, "Nou.")
	return

def init(db):
	return True

mappings = (Mapping(type=["privmsg"], command="reload", function=reloadmods),)
