#state example
from util import Mapping

def statecommand(event, bot):
	command = ""
	if event.input:
		command = event.input.split(" ", 1)
		if len(command) > 1:
			command, input = command
		else:
			command, input = command[0], None
	
	if command == "channel":
		if not input:
			for chan in bot.state.channels.keys():
				bot.say("Channel: %s" % chan)
				for user in bot.state.channels[chan].users:
					bot.say("- %s" % user)
		else:
			if input in bot.state.channels:
				bot.say("Channel: %s:" % input)
				for user in bot.state.channels[input].users:
					bot.say("- %s" % user)
			else:
				bot.say("lol dunno channel %s" % input)
		
	elif command == "network":
		bot.say("Known users on network: %s" % ", ".join(bot.state.users.keys()))

	elif command == "lol":
		print bot.supported.getFeature("PREFIX")
		
	elif command == "channels":
		bot.say(", ".join(bot.state.channels.keys()))

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="state", function=statecommand),)
