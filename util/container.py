#container...
#This module does a few things. It holds a reference to the current botinstance
#it wraps actual botinst functions to limit the scope of what functions modules have access to within botinstance
#it also holds a queue for messages attempted to be sent while there is no current botinstance

from Queue import Queue, Empty
from time import time
from functools import partial

from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

from util.event import WaitEvent
from util.state import Network
from util.client import BurlyBot

class TimeoutException(Exception):
	pass

class WaitData:
	def __init__(self, interestede, stope):
		self.done = False
		self.q = Queue()
		self.interestede = set(interestede)
		self.stope = set(stope)

class Container:
	def __init__(self, settings):
		self.network = settings.serverlabel
		self._settings = settings
		self.state = Network(settings.serverlabel)
		self._botinst = None
		self._outqueue = Queue() #deque or Queue, whatever

	def __getattr__(self, name):
		#if name isn't in container, look in botinst IF BOTINST EXISTS
		if name in self.__dict__: 
			return getattr(self, name)
		else:
			attr = getattr(BurlyBot, name) #raise if doesn't have
			if self._botinst:
				attr = getattr(self._botinst, name)
				if hasattr(attr, '__call__'):
					return partial(reactor.callFromThread, attr)
				else:
					return attr
			else:
				if hasattr(attr, '__call__'):
					# return queueable
					return partial(self._queuer, name)
				else:
					# SPECIAL CASE: if module requests attribute from BurlyBot
					#  but there is no botinst, None will be returned.
					# TODO: This should maybe raise exception else how determine what is None for real?
					#		Interesting to consider trying to block until available...
					return None 

	#TODO: why is there two of these
	def _setbotinst(self, botinst):
		self._botinst = botinst
	
	def _queuer(self, funcname, *args, **kwargs):
		self._outqueue.append((funcname, args, kwargs))
	
	# say needs a source (channel, user, etc.) A source is supplied in BotWrapper
	def say(self, msg):
		raise ValueError("No source defined.")
	
	def _setBotinst(self, botinst):
		self._botinst = botinst
		# TODO: (another), because of the nature of queues and "empty", we should probably check this queue whenever any action is triggered
		#	in case things get left in the _outqueue
		if botinst:
			while not self._outqueue.empty():
				outbound = self._outqueue.get()
				print "PROCESSING QUEUED THINGS"
				# These will always be BurlyBot functions so let's do some magic.
				# There shouldn't be any AttributeError, and if there is, bad luck I guess.
				getattr(self.botinst, outbound[0])(*outbound[1], **outbound[2])

	# Option getter/setters	
	def getOption(self, opt):
		return blockingCallFromThread(reactor, self._settings.getOption, opt)
	def getModuleOption(self, module, option):
		return blockingCallFromThread(reactor, self._settings.getModuleOption, module, option)
		
	# Use blockingCallFromThread on these so the modules can get the Exceptions
	#  (in which case the bot will just receive it back if unhandled, bummer)
	#  What exceptions you might ask? Well we'll only allow setting of values that exist
	def setOption(self, opt, value):
		return blockingCallFromThread(reactor, setattr, self._settings, opt, value)
	def setModuleOption(self, module, option, value):
		return blockingCallFromThread(reactor, setattr, self._settings.getModuleOption, module, option)
		
	# Some module helpers
	def getModule(self, modname):
		return blockingCallFromThread(reactor, self._settings.getModule, modname)
	
	def isModuleAvailable(self, modname):
		return blockingCallFromThread(reactor, self._settings.isModuleAvailable, modname)
	
	#callback to handle module errors
	def _moduleerr(self, e):
		print "error:", e #exception, or Failure thing
		
	def send_and_wait(self, interestede, stope, timeout=10, sendfunc, *sendargs, **sendkwargs):
		"""This method will block and yield events as they come..."""
		expired = time() + timeout
		while not self._botinst:
			if expired < time():
				raise TimeoutException()
			sleep(0.5)
		try:
			wd = WaitData(interestede, stope)
			#add wait events to dispatcher. ONLY MODIFY DISPATCHER IN REACTOR THREAD PLEASE.
			reactor.callFromThread(Dispatcher.addWaitData, we)
			#send...
			sendfunc(*sendargs, **sendkwargs)
			# and now we play the waiting game...
			# TODO: how should expired/timeouts work? Should timeout "reset" after the last
			# seen event? Or should it act as "run for this long total"
			while not wd.done:
				try: 
					item = results.get(timeout=0.5)
					yield item
				except Empty: 
					if expired < time():
						raise TimeoutException()
			return
		finally:
			# in the case that garbage collection happens (in the event that user bails the generator
			#	before the stop event fires) we can "clean up" and remove the event from the waitdispatcher
			reactor.callFromThread(Dispatcher.delWaitData, we)
			

# provide special container to use when feeding "init()" of modules
# doesn't try to call methods inside reactor because already inside reactor
class SetupContainer(object):
	def __init__(self, realcontainer):
		self.container = realcontainer
		
	# Some module helpers
	def getModule(self, modname):
		return self._settings.getModule(modname)
	
	def isModuleAvailable(self, modname):
		return self._settings.isModuleAvailable(modname)
		
	def __getattr__(self, name):
		# get Server setting if set, else fall back to global Settings
		if name in self.__dict__: 
			return getattr(self, name)
		else:
			return getattr(self.container, name)
		