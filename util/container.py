#container...
#This module does a few things. It holds a reference to the current botinstance
#it wraps actual botinst functions to limit the scope of what functions modules have access to within botinstance
#it also holds a queue for messages attempted to be sent while there is no current botinstance

from Queue import Queue, Empty
from collections import deque
from time import time
from functools import partial

from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
from twisted.python.failure import Failure

from util.state import Network
from util.client import BurlyBot
from util.helpers import isIterable

class TimeoutException(Exception):
	pass

class WaitData:
	def __init__(self, interestede, stope):
		self.done = False
		self.q = Queue()
		#assume interestede (&stope) may be string for single event 
		# (because I accidently made that mistake!)
		if isIterable(interestede):
			self.interestede = set(interestede)
		else:
			self.interestede = set((interestede,))
		if isIterable(stope):
			self.stope = set(stope)
		else:
			self.stope = set((stope,))

class Container:
	def __init__(self, settings):
		self.network = settings.serverlabel
		self._settings = settings
		self.state = Network(settings.serverlabel)
		self._botinst = None
		self._outqueue = deque() #deque or Queue, whatever

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
					# return function to queue the real method call
					return partial(reactor.callFromThread, self._queuer, name)
				else:
					# SPECIAL CASE: if module requests attribute from BurlyBot
					#  but there is no botinst, None will be returned.
					# TODO: This should maybe raise exception else how determine what is None for real?
					#		Interesting to consider trying to block until available...
					return None 

	def _queuer(self, funcname, *args, **kwargs):
		self._outqueue.append((funcname, args, kwargs))
	
	# say needs a source (channel, user, etc.) A source is supplied in BotWrapper
	def say(self, msg):
		raise ValueError("No source defined.")
	
	def _setBotinst(self, botinst):
		self._botinst = botinst
		# checkqueue 2 seconds after signedOn to give time to join channels and stablize
		# also keep checking this outqueue 2 seconds later if there is still elements left
		reactor.callLater(2, self._checkQueue)
	
	def _checkQueue(self):
		checkAgain = False
		if self._botinst:
			while self._outqueue:
				outbound = self._outqueue.popleft()
				print "PROCESSING QUEUED METHODS"
				# These will always be BurlyBot functions so let's do some magic.
				# There shouldn't be any AttributeError, and if there is, bad luck I guess.
				# This should always be called from inside the reactor so don't need to pass it to the reactor
				getattr(self._botinst, outbound[0])(*outbound[1], **outbound[2])
				checkAgain = True
		# check again in case we missed some
		if checkAgain:
			reactor.callLater(2, self._checkQueue)

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
	#TODO: maybe provide modules a way to hook these?
	#	like if we let a module provide a function, we can pass the Failure object to it.
	def _moduleerr(self, e):
		if isinstance(e, Failure):
			e.cleanFailure()
			e.printTraceback()
		else:
			print "error:", e
	
	# stop event optional since you can just bail out of the generator if you know you have all
	# the things you want
	# f is the send function you want to call to start the waiting
	# Warning: if you are not using stopevents and you are doing many blocking operations before your
	# function using send_and_wait finishes, the generator won't have been GC'd for cleanup so bad things might happen.
	# generator.close() if you suspect that your function won't be finished for some time after bailing from a generator.
	# BIG WARNING: iterate over the generator with something like "for e in bot.send_and_wait(...
	#	May leak very fast if you have unhandled exceptions inside the loop, (the above mitigates this I think...)
	def send_and_wait(self, interestede, stope=[], timeout=10, f=None, fargs=[], **kwargs):
		"""This method will block and yield events as they come..."""
		if not f:
			raise ValueError("Missing function")
		expired = time() + timeout
		while not self._botinst:
			if expired < time():
				raise TimeoutException()
			sleep(0.5)
		try:
			wd = WaitData(interestede, stope)
			#add wait events to dispatcher. ONLY MODIFY DISPATCHER IN REACTOR THREAD PLEASE.
			reactor.callFromThread(self._settings.dispatcher.addWaitData, wd)
			#send...
			f(*fargs, **kwargs)
			# and now we play the waiting game...
			# TODO: how should expired/timeouts work? Should timeout "reset" after the last
			# seen event? Or should it act as "run for this long total"
			while not wd.done:
				try: 
					item = wd.q.get(timeout=0.5)
					yield item
				except Empty: 
					if expired < time():
						raise TimeoutException()
			while not wd.q.empty():
				try:
					yield wd.q.get()
				except Empty:
					break
			return
		finally:
			# in the case that garbage collection happens (in the event that user bails the generator
			#	before the stop event fires) we can "clean up" and remove the event from the waitdispatcher
			reactor.callFromThread(self._settings.dispatcher.delWaitData, wd)
			

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
		