from util import Mapping
#core internal BBM commands
# things like .reload

def reloadmods(event, botinst, db):
	botinst.factory.dispatcher.reload() #lol will this even work
	return

def init(db):
	pass

mappings = (Mapping(type=["MSG"], command="reload", function=reloadmods),)
