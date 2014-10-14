#timerexample.py

from util import Mapping, Timers, commandSplit, argumentSplit

# requires keyword arguments
def timercallback(bot=None, channel=None, msg=None):
	bot.sendmsg(channel, msg)

def timers(event, bot):
	command, args = commandSplit(event.argument)
	
	if command == "show":
		bot.say("Timers:")
		for timer in Timers.getTimers().itervalues():
			bot.say(" - %s: reps = %s, delay = %s, f = %s" % (timer.name, timer.reps, timer.interval, timer.f))
		
	elif command == "add":
		args = argumentSplit(args, 4) #add timername delay reps msg
		if not args:
			bot.say("Not enough arguments. Need: timername delay reps message (reps <= 0 means forever)")
			return
		msg = Timers.addtimer(args[0], float(args[1]), timercallback, reps=int(args[2]), msg=args[3], bot=bot, channel=event.channel)[1]
		bot.say("%s (%s)" % (msg, args[0]))

	elif command == "stop":
		bot.say(Timers.deltimer(args)[1])

#mappings to methods
mappings = (Mapping(command="timers", function=timers),)
