#timer.py

#lol don't use this for remind pls
#I guess suggested use would be for alarm.py

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread

class Timer:
	
	def __init__(self, name, interval, f, kwargs, reps, startnow):
		self.name = name
		self.f = f
		self.kwargs = kwargs
		self.reps = reps
		self.interval = interval
		self.lc = LoopingCall(Timers.doInThread, self)
		self.lc.start(interval, startnow)
		
	

class Timers:
	timers = {}
	
	@classmethod
	def _addInternaltimer(cls, name, interval, f, kwargs={}, reps=None, startnow=False):
		#kinda want to use _ prefix for internal things like DBcommit
		if name in cls.timers:
			return (False, "Timer %s already exists." % name)
		else:
			cls.timers[name] = Timer(name, interval, f, kwargs, reps, startnow)
			return (True, "Timer added.")
	
	@classmethod
	def addtimer(cls, name, interval, f, reps=None, startnow=False, **kwargs):
		#kinda want to use _ prefix for internal things like DBcommit
		if name.startswith("_"):
			return (False, "Invalid name")
		if name in cls.timers:
			return (False, "Timer already exists.")
		else:
			cls.timers[name] = Timer(name, interval, f, kwargs, reps, startnow)
			return (True, "Timer added.")
			
	@classmethod
	def deltimer(cls, name):
		if name in cls.timers:
			#maybe add tryexcept here incase timer already finished
			cls.timers[name].lc.stop()
			del cls.timers[name]
			return (True, "Timer removed.")
		else:
			return (False, "Timer %s not found" % name)
			
	@classmethod
	def doInThread(cls, timerobj):
		print "Calling f: %s" % timerobj.f
		reactor.callInThread(timerobj.f, **timerobj.kwargs)
		if timerobj.reps:
			timerobj.reps -= 1
			if timerobj.reps == 0:
				cls.timers[timerobj.name].lc.stop()
				del cls.timers[timerobj.name]
	
	@classmethod
	def _stopall(cls):
		for timername in cls.timers:
			cls.timers[timername].lc.stop()
