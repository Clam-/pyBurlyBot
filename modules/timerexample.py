#timerexample.py

#BROKEN: needs total overhaul

from util import Mapping, Timers

def timercallback(network, channel, msg):
	#get botinst/wrapper
	#botinst = Settings.servers[network].state.container
	
	botinst.msg(channel, msg)


def timers(event, botinst):
	command = ""
	if event.input:
		command = event.input.split(" ", 1)
		if len(command) > 1:
			command, input = command
		else:
			command, input = command[0], None
	
	if command == "show":
		if not input:
			botinst.msg(event.channel, "Timers:")
			for timer in Timers.timers:
				t = Timers.timers[timer]
				s = " - %s: reps = %s, delay = %s, f = %s" % (t.name, t.reps, t.interval, t.f)
				botinst.msg(event.channel, s)
		
	elif command == "add":
		ta = input.split(" ", 3) #add timername delay reps msg
		if len(ta) != 4:
			botinst.msg(event.channel, "Not enough things. Need timername delay reps message")
			return
		if ta[2] == 0: reps = None
		else: reps = int(ta[2])
		Timers.addtimer(ta[0], float(ta[1]), timercallback, reps=reps, msg=ta[3], network=botinst.network, channel=event.channel)
		botinst.msg(event.channel, "Timer %s added." % ta[0])

	elif command == "stop":
		print Timers.deltimer(input)


def init():
	#lol do what now...
	return True

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="timers", function=timers),)
