# random module
from random import choice, randint

from util import Mapping, functionHelp, argumentSplit

COIN = ("heads", "tails")

def doflip(event, bot):
	""" coinflip. choice flip will return randomly "heads" or "tails"."""
	bot.say("%s" % choice(COIN))

def dochoice(event, bot):
	""" choice values. choice will randomly select one of the given values."""
	if not event.argument: return bot.say(functionHelp(dochoice))
	values = argumentSplit(event.argument, -1)
	return bot.say("%s" % choice(values))

def dorand(event, bot):
	""" rand [arg]. If no arg rand will generate random int between 0-10. If arg is an integer
	value a random int between 0-arg will be generated. arg can also be a list of items, in which case will act like choice."""
	if not event.argument:
		return bot.say("%s" % randint(0, 10))
	try:
		return bot.say("%s" % randint(0, int(event.argument)))
	except ValueError:
		dochoice(event, bot)
	

mappings = (Mapping(command=("rand", "random"), function=dorand), 
	Mapping(command="choice", function=dochoice),
	Mapping(command=("coinflip", "heads", "tails", "flip"), function=doflip),)

