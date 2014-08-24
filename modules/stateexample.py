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
				bot.msg(event.channel, "Channel: %s" % chan)
				for user in bot.state.channels[chan].users:
					bot.msg(event.channel, "- %s" % user)
		else:
			if input in bot.state.channels:
				bot.msg(event.channel, "Channel: %s:" % input)
				for user in bot.state.channels[input].users:
					bot.msg(event.channel, "- %s" % user)
			else:
				bot.msg(event.channel, "lol dunno channel %s" % input)
		
	elif command == "network":
		bot.msg(event.channel, "Known users on network: %s" % ", ".join(bot.state.users.keys()))

	elif command == "lol":
		print bot.supported.getFeature("PREFIX")
		
	elif command == "channels":
		bot.msg(event.channel, ", ".join(bot.state.channels.keys()))

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="state", function=statecommand),)
