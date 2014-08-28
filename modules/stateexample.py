#state example
from util import Mapping, commandSplit

def statecommand(event, bot):
	command, args = commandSplit(event.argument)
	
	if command == "channel":
		if not args:
			for chan in bot.state.channels.keys():
				bot.say("Channel (%s): %s" % (chan,
					", ".join(bot.state.channels[chan].users)))
		else:
			if args in bot.state.channels:
				bot.say("Channel (%s): %s" % (args, 
					", ".join(bot.state.channels[args].users)))
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
