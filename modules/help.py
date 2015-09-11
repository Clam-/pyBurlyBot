# help module
from util import Mapping, functionHelp, argumentSplit
from util.helpers import isIterable

def _filter_mappings(bot, pm=False, cmd=None):
	for mapping in bot._settings.dispatcher._getCommandMappings(cmd):
		if not mapping.hidden:
			if mapping.admin and pm and bot._isadmin:
				cmds.append(mapping.command[0])
			else:
				cmds.append(mapping.command[0])

def list_commands(bot, pm=False):
	cmds = set()
	for mapping in blockingCallFromThread(reactor, _filter_mappings, bot, pm):
		cmds.append(mapping.command[0])
	cmds = list(cmds)
	cmds.sort()
	bot.say(" ".join(cmds))

def help(event, bot):
	""" help [argument].  If argument is specified, get the help string for that command.
	Otherwise list all commands (same as commands function).
	"""
	cmd, arg = argumentSplit(event.argument, 2)
	# other modules should probably not do this:
	if cmd:
		cmd_mappings = blockingCallFromThread(reactor, _filter_mappings, bot, event.isPM, cmd)
		if cmd_mappings:
			for mapping in cmd_mappings:
				if arg:
					h = functionHelp(mapping.function, arg)
					if h: bot.say(h)
					else: bot.say("No help for (%s) available." % cmd)
				else:
					h = functionHelp(mapping.function)
					if h:
						command = mapping.command
						if isIterable(command) and len(command) > 1:
							bot.say("%s Aliases: %s" % (h, ", ".join(command)))
						else:
							bot.say(h)
					else:
						bot.say("No help for (%s) available." % cmd)
		else:
			bot.say("Command %s not found." % cmd)
	else:
		list_commands(bot, event.isPM(), bot.isadmin())

def commands(event, bot):
	""" commands.  List available pyBurlyBot commands by their primary name.
	"""
	list_commands(bot, event.isPM(), bot.isadmin())



mappings = (Mapping(command="help", function=help),
			Mapping(command="commands", function=commands))
