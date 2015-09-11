# help module
from util import Mapping, functionHelp, argumentSplit
from util.helpers import isIterable


def list_commands(bot):
	cmds = bot._settings.dispatcher.getCommands()
	try: cmds.remove("eval")
	except ValueError: pass
	cmds.sort()
	bot.say(" ".join(cmds))


def help(event, bot):
	""" help [argument].  If argument is specified, get the help string for that command.
	Otherwise list all commands (same as commands function).
	"""
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
						if isIterable(command) and len(command) > 1:
							bot.say("%s Aliases: %s" % (h, ", ".join(command)))
						else:
							bot.say(h)
					else:
						bot.say("No help for (%s) available." % cmd)
		else:
			bot.say("Command %s not found." % cmd)
	else:
		list_commands(bot)

def commands(event, bot):
	""" commands.  List available pyBurlyBot commands by their primary name.
	"""
	list_commands(bot)



mappings = (Mapping(command="help", function=help),
			Mapping(command="commands", function=commands))
