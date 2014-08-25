#timerexample.py

from util import Mapping, Timers, commandSplit, argumentSplit

# requires keyword arguments
def timercallback(bot=None, channel=None, msg=None):
	bot.msg(channel, msg)

def timers(event, bot):
	command, args = commandSplit(event.input)
	
	if command == "show":
		bot.msg(event.channel, "Timers:")
		for timer in Timers.getTimers().values():
			s = " - %s: reps = %s, delay = %s, f = %s" % (timer.name, timer.reps, timer.interval, timer.f)
			bot.msg(event.channel, s)
		
	elif command == "add":
		args = argumentSplit(args, 4) #add timername delay reps msg
		if not args:
			bot.msg(event.channel, "Not enough arguments. Need: timername delay reps message (reps <= 0 means forever)")
			return
		msg = Timers.addtimer(args[0], float(args[1]), timercallback, reps=int(args[2]), msg=args[3], bot=bot, channel=event.channel)[1]
		bot.say("%s (%s)" % (msg, args[0]))

	elif command == "stop":
		bot.say(Timers.deltimer(args)[1])

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="timers", function=timers),)
