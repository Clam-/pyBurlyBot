#state example
from util import Mapping, commandSplit

#Note: Smart use of only referencing dict, set and list attributes once (or as few times as possible) will make
#	state use much much quicker (probably)

def statecommand(event, bot):
	command, args = commandSplit(event.argument)
	
	if command == "channel":
		if not args:
			for chan in bot.state.channels.itervalues():
				bot.say("Users on channel (%s): %s" % (chan.name,
					", ".join(chan.users)))
		else:
			chan = bot.state.channels.get(args, None)
			if chan:
				bot.say("Users on channel (%s): %s" % (args, 
					", ".join(chan.users)))
			else:
				bot.say("lol dunno channel %s" % args)
	
	if command == "bans":
		if not args:
			for chan in bot.state.channels.itervalues():
				bot.say("Bans on channel (%s): %s" % (chan.name,
					", ".join(chan.banlist.iterkeys())))
		else:
			chan = bot.state.channels.get(args, None)
			if chan:
				bot.say("Bans on channel (%s): %s" % (args, 
					", ".join(chan.banlist.iterkeys())))
			else:
				bot.say("lol dunno channel %s" % args)
	
	elif command == "network":
		bot.say("Known users on network: %s" % ", ".join(bot.state.users.keys()))
		
	elif command == "channels":
		bot.say("On channels: %s" % ", ".join(bot.state.channels.keys()))
	else:
		bot.say("state: channel, network, channels")

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="state", function=statecommand),)
