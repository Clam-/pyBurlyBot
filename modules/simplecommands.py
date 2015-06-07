# module for simple displaying of text on command
# configurable from moduleoptions

### Modules should not import this! Unless they have a very good reason to.
from util.settings import Settings

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
###

from functools import partial
from util import Mapping, argumentSplit, functionHelp
from json import loads, dumps

OPTIONS = {
	"commands" : (list, 'List of [command, output]. E.g. ["someurl", "URL: http://google.com"] will output "URL: http://google.com" on usage of the "someurl" command.'
		'command may be a string of a single command or a list of multiple commands to bind to a single output string.', [["hello", "world."]]),
}

# TODO: Was lazy, can't remember cross-module trickiness
def _reallyReload():
	Settings.reloadStage1()
	Settings.reloadStage2()

def simplecommands(event, bot):
	""" simplecommands [(~del, ~list)] input[,alias1,alias2,etc] output.  Simple interface for adding/removing simplecommands.
	If only input is supplied, output is retrieved.  If ~del is specified, input is deleted if found.
	e.g. .simplecommands google google.com
	"""
	arg1, arg2 = argumentSplit(event.argument, 2)
	if arg1 == '~list':
		commands = bot.getOption("commands", module="simplecommands")
		cmdlist = []
		commands.sort()

		for command, output in commands:
			if (isinstance(command, list) or isinstance(command, tuple)) and len(command) > 1:
				cmdlist.append('(%s)' % ', '.join(command))
			else:
				print repr(command)
				cmdlist.extend(command)
		return bot.say('Simplecommands: %s' % ', '.join(cmdlist))

	if not bot.isadmin():
		return bot.say('Uwish.')

	if not arg1:
		return bot.say(functionHelp(simplecommands))

	# [[["paste", "dpaste"], "http://dpaste.com"], [. . . ]]
	commands = bot.getOption("commands", module="simplecommands")
	# Delete a simplecommand
	if arg1 == '~del' and arg2:
		match = None
		temp_match = None
		newcmds = arg2.split(',')
		for index, command in enumerate(commands):
			for newcmd in newcmds:
				if (isinstance(command[0], list) and newcmd in command[0]) or newcmd == command[0]:
					temp_match = commands[index]
			if temp_match:
				if match:
					return bot.say('Simplecommand specified (%s) matches more than one simplecommand: (%s) and (%s)'
					% (arg2, ', '.join(temp_match[0]), ', '.join(match[0])))
				match = temp_match
				temp_match = None

		if not match:
			return bot.say('(%s) is not a known simplecommand.' % arg2)
		commands.remove(match)
		bot.setOption("commands", commands, module="simplecommands")
		blockingCallFromThread(reactor, Settings.saveOptions)
		bot.say('Simplecommand (%s) deleted.  Options saved.  Reloading...' % arg2)
		blockingCallFromThread(reactor, _reallyReload)
		return bot.say('Done.')
	elif arg2:
		match = None
		temp_match = None
		newcmds = arg1.split(',')
		for index, command in enumerate(commands):
			for newcmd in newcmds:
				if (isinstance(command[0], list) and newcmd in command[0]) or newcmd == command[0]:
					temp_match = commands[index]
			if temp_match:
				if match:
					return bot.say('Simplecommand specified (%s) matches more than one simplecommand: (%s) and (%s)'
					% (arg1, ', '.join(temp_match[0]), ', '.join(match[0])))
				match = temp_match
				temp_match = None

		# Replace an existing simplecommand
		if match:
			if len(match[0]) > 1:
				return bot.say("Can't modify simplecommand with multiple input mappings (%s), \
					delete it first with \x02~del %s\x02 and recreate it." % (', '.join(match[0]), arg1))
			commands.remove(match)
			commands.append([arg1.split(','), arg2])
			bot.setOption("commands", commands, module="simplecommands")
			blockingCallFromThread(reactor, Settings.saveOptions)
			bot.say('Simplecommand (%s) replaced.  Options saved.  Reloading...' % arg1)
			blockingCallFromThread(reactor, _reallyReload)
			bot.say('Done.')
		# Add a new simplecommand
		else:
			# TODO: Yeah, this probably isn't good -- or maybe it's fine
			for cmd in newcmds:
				ret = bot._settings.dispatcher.getCommandFuncs(cmd.lower())
				if ret:
					return bot.say('Command (%s) already in use by the \x02%s\x02 module.' % (cmd, ret[0][0].__module__[11:]))
			commands.append([arg1.split(','), arg2])
			bot.setOption("commands", commands, module="simplecommands")
			blockingCallFromThread(reactor, Settings.saveOptions)
			bot.say('Simplecommand (%s) added.  Options saved.  Reloading...' % arg1)
			blockingCallFromThread(reactor, _reallyReload)
			bot.say('Done.')
	else:
		match = None
		for command, output in commands:
			if isinstance(command, list) and arg1 in command:
				match = (command, output)
		if not match:
			return bot.say('(%s) is not a known simplecommand.' % arg1)
		bot.say('Simplecommand (%s): %s' % (', '.join(match[0]), match[1]))


def echothis(text, event, bot):
	bot.say(text)

# for abuse in init:
mappings = [Mapping(command=("simplecommand", "simplecommands"), function=simplecommands)]

def init(bot):
	global mappings # oops! Bad things are going to happen
	# you should very much not do the following. This relies on knowing how the internals of dispatcher setup work!
	for command, output in bot.getOption("commands", module="simplecommands"):
		mappings.append(Mapping(command=command, function=partial(echothis, output)))
	return True
