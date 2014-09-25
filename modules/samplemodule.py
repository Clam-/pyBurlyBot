#sample module
from re import compile as recompile
from util import Mapping, commandSplit, functionHelp
from util import DBQuery

# options types for dynamic configuration setting via config module
# options not specified here will have no help text nor type checking and will not have defaults automatically set
OPTIONS = {
	"repeat" : (bool, "If true will repeat privmsg lines starting with '|'.", True),
	"ignorestarting" : (list, "Lines starting with items in this list will be ignored.", []),
}

def repeater(event, bot):
	#repeat things
	if bot.getOption("repeat", module="samplemodule"):
		bot.say("%s : %s" % (event.nick, event.msg))


def samplecommand(event, bot):
	""" samplecommand [option] [argument]. samplecommand will do things depending on what option is used. 
	Available option: something, dothing
	|samplecommand something [argument]: will output "something", and if argument is present, will follow.
	|samplecommand dothing [argument]: will output argument if it exists, followed by "dothing"
	"""
	#do some things
	command, args = commandSplit(event.argument)
	if command == "something":
		if args: bot.say("%s %s" % (command, args))
		else : bot.say("%s" % command)
	elif command == "dothing":
		if args: bot.say("%s %s" % (args, command))
		else : bot.say("%s" % command)
	else:
		bot.say(functionHelp(samplecommand))

#init should always be here to setup needed DB tables or objects or whatever
def init(bot):
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	result = DBQuery("SELECT name FROM sqlite_master WHERE name='sample_table'")
	if result.error:
		#uh oh....
		print "What happened?: %s" % result.error
	else:
		#good
		if not result.rows:
			DBQuery('''
			create table sample_table(
			columnA,
			columnB
			);''')
		return True

#mappings to methods
mappings = (Mapping(types=["privmsged"], regex=recompile(r"\|.*"), function=repeater),
	Mapping(command="samplecommand", function=samplecommand),)
