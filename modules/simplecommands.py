# module for simple displaying of text on command
# configurable from moduleoptions

from functools import partial
from util import Mapping

# for abuse in init:
mappings = []

OPTIONS = {
	"commands" : (list, 'List of [command, output]. E.g. ["someurl", "URL: http://google.com"] will output "URL: http://google.com" on usage of the "someurl" command.'
		'command may be a string of a single command or a list of multiple commands to bind to a single output string.', [["hello", "world."]]),
}

def echothis(text, event, bot):
	bot.say(text)

def init(bot):
	global mappings # oops! Bad things are going to happen
	# you should very much not do the following. This relies on knowing how the internals of dispatcher setup work!
	for command, output in bot.getOption("commands", module="simplecommands"):
		mappings.append(Mapping(command=command, function=partial(echothis, output)))
	return True
