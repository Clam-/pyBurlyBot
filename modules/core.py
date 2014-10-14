#core internal BurlyBot commands
# things like .reload
from util import Mapping, functionHelp, argumentSplit
from util.helpers import isIterable
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

def help(event, bot):
	#inspect.getdoc
	#eventmap[etype]["command"].setdefault(commandname, []).append(mapping)
	cmd, arg = argumentSplit(event.argument, 2)
	# other modules should not do this:
	if cmd:
		cmds = bot._settings.dispatcher.getCommandFuncs(cmd)
		if cmds:
			for func, command in cmds:
				if arg:
					h = functionHelp(func, arg)
					if h: bot.say(h)
					else: bot.say("No help for (%s) available." % cmd)
				else:
					h = functionHelp(func)
					if h:
						if isIterable(command):
							bot.say("%s Aliases: %s" % (h, ", ".join(command)))
						else:
							bot.say(h)
					else:
						bot.say("No help for (%s) available." % cmd)
		else:
			bot.say("Command %s not found." % cmd)
		
	else:
		cmds = bot._settings.dispatcher.getCommands()
		try: cmds.remove("eval")
		except ValueError: pass
		cmds.sort()
		bot.say(" ".join(cmds))
	
mappings = (Mapping(command="reload", function=reloadbot),
	Mapping(command="help", function=help))

