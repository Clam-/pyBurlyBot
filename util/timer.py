#timer.py

# suggested use would be for an alarm module or somesuch.

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread, blockingCallFromThread

class Timer(object):
	# reps <= 0 means forever
	def __init__(self, name, interval, f, reps=1, startnow=False, **kwargs):
		self.name = name
		self.f = f
		self.kwargs = kwargs
		self.reps = reps
		self.interval = interval
		self.lc = LoopingCall(Timers.runTimer, self)
		self.lc.start(interval, startnow)

class TimerInfo(object):
	def __init__(self, timer):
		self.name = timer.name
		self.f = timer.f
		self.kwargs = timer.kwargs
		self.reps = timer.reps
		self.interval = timer.interval

class Timers:
	timers = {}
	
	@classmethod
	def _addTimer(cls, name, interval, f, reps=1, startnow=False, **kwargs):
		if name in cls.timers:
			return (False, "Timer already exists.")
		else:
			cls.timers[name] = Timer(name, interval, f, reps, startnow, **kwargs)
			return (True, "Timer added.")
	
	# _timers are for internal use only
	@classmethod
	def addtimer(cls, name, interval, f, reps=1, startnow=False, **kwargs):
		#kinda want to use _ prefix for internal things like DBcommit
		try:
			if name.startswith("_"):
				return (False, "Invalid name.")
		except AttributeError:
			return (False, "Invalid name.")
		else:
			# force interval and rep in to float and int respectivly in case module forgot (I forgot)
			return blockingCallFromThread(reactor, cls._addTimer, name, float(interval), f, int(reps), startnow, **kwargs)
		
	@classmethod
	def _deltimer(cls, name):
		if name in cls.timers:
			#maybe add tryexcept here incase timer already finished
			cls.timers[name].lc.stop()
			del cls.timers[name]
			return (True, "Timer removed.")
		else:
			return (False, "Timer %s not found." % name)
		
	@classmethod
	def deltimer(cls, name):
		try:
			if name.startswith("_"):
				return (False, "Invalid name.")
		except AttributeError:
			return (False, "Invalid name (%s)." % name)
		return blockingCallFromThread(reactor, cls._deltimer, name)
	
	#run the desired function in a thread but manage the timer in the reactor
	@classmethod
	def runTimer(cls, timerobj):
		#print "Calling f: %s" % timerobj.f
		reactor.callInThread(timerobj.f, **timerobj.kwargs)
		if timerobj.reps > 0:
			timerobj.reps -= 1
			if timerobj.reps == 0:
				cls.timers[timerobj.name].lc.stop()
				del cls.timers[timerobj.name]
	
	@classmethod
	def _stopall(cls):
		for timername in cls.timers:
			try:
				cls.timers[timername].lc.stop()
			except AssertionError:
				continue
			
	@classmethod
	def _getTimers(cls):
		d = {}
		for t in cls.timers:
			d[t] = TimerInfo(cls.timers[t])
		return d
		
	@classmethod
	def getTimers(cls):
		return blockingCallFromThread(reactor, cls._getTimers)
