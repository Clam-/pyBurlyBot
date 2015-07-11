# help module
from util import Mapping, functionHelp, argumentSplit
from util.helpers import isIterable

def help(event, bot):
	cmd, arg = argumentSplit(event.argument, 2)
	# other modules should probably not do this:
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

mappings = Mapping(command="help", function=help),
