# basic autoop/voice/hop module

from util import Mapping
from util.settings import ConfigException

#TODO: Make this work on hostmasks

OPTIONS = {
	"autoop" : (list, "List of channels to autoop on. Use lowercase.", []),
	"autovoice" : (list, "List of channels to autovoice on. Use lowercase.", []),
	"autohalf" : (list, "List of channels to autohalf op on. Use lowercase.", []),
}

# TODO: Consider making custom IRCClient.mode function that can do this in one call
#		Something like takes user argument as list.
def dostatus(event, bot):
	target = event.target
	chan = bot.state.channels.get(target)
	if not chan or (bot.nickname not in chan.ops): return
	modes = []
	target = target.lower()
	if target in bot.getOption("autoop", module="autojoinstatus"):
		modes.append("o")
	if target in bot.getOption("autovoice", module="autojoinstatus"):
		modes.append("v")
	if target in bot.getOption("autohalf", module="autojoinstatus"):
		modes.append("h")
	for mode in modes:
		bot.mode(target, True, mode, user=event.nick)

def init(bot):
	if not bot.getOption("enablestate"):
		raise ConfigException('autjoinstatus module requires "enablestate" option')
	return True

mappings = (Mapping(types=["userJoined"], function=dostatus),)
