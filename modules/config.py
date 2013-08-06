#config module
from util import Mapping
from util.settings import Settings

from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

#!config get nick
#!config set nick nickname

def showhelp(bot):
	#show help? We should make some really nice framework for handling input
	# and help and stuff
	bot.say("get/set param [newvalue]")

def config(event, bot):
	#do some things
	command = ""
	if not bot.isadmin():
		bot.say("Good joke.")
		return
	if event.input:
		command = event.input.split(" ", 1)
		if len(command) > 1:
			command, input = command
		else:
			command, input = command[0], None
	else: return showhelp(bot)
	
	if command == "save":
		blockingCallFromThread(reactor, Settings.saveOptions)
		bot.say("Done. (I think)")
		return
	
	if not input: return showhelp(bot)
	param = input.split(" ", 1)
	if len(param) > 1:
		param, input = param
	else: 
		param, input = param[0], None
		
	if command == "get":
		bot.say("%s : %s" % (param, bot.getOption(param)))
		return
	elif command == "set":
		if not input: return showhelp(bot)
		old = bot.getOption(param)
		bot.setOption(param, input)
		bot.say("%s : %s (was: %s)" % (param, input, old))
		return
	else:
		return showhelp(bot)
	
def init():
	return True

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="config", function=config),)
