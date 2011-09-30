#container...
#This module does a few things. It holds a reference to the current botinstance
#it wraps actual botinst functions to limit the scope of what functions modules have access to within botinstance
#it also holds a queue for messages attempted to be sent while there is no current botinstance

from Queue import Queue, Empty
from twisted.internet import reactor
from time import time

from dispatcher import Dispatcher
from event import WaitEvent

class Container:
	
	def __init__(self, settings):
		self.network = settings.name
		self.settings = settings
		self.state = None
		self.botinst = None
		self.outqueue = Queue() #deque or Queue, whatever
	
	# TODO: if you want to do say, you need to somehow get the event... Otherwise you could easily have a say method on event that redirects to here
	# passing itself
	def say(self, msg):
		raise ValueError("No source defined.")
	
	def addbotinst(self, botinst):
		self.botinst = botinst
		# TODO: change this so that we are directly calling botinst's methods instead of wrapper
		# 	Do this so that there are no weird issues when calling callFromThread within the main 
		#	reactor thread (which is when this will take place)
		# TODO: (another), because of the nature of queues and "empty", we should probably check this queue whenever any action is triggered
		#	in case things get left in the outqueue
		if botinst:
			while not self.outqueue.empty():
				outbound = self.outqueue.get()
				print "PROCESSING QUEUED THINGS"
				outbound[0](*outbound[1])
	
	# TODO: I wonder if you can do this common "check if botinst if not, queue" in a decorator.. I had a quick look but I don't really fully grasp
	#decorators yet
	def msg(self, dest, msg):
		if not self.botinst:
			self.outqueue.append((self.msg, (dest, msg)))
			return
		reactor.callFromThread(self.botinst.sendmsg, dest, msg)
			
	def notice(self, dest, msg):
		if not self.botinst:
			self.outqueue.append((self.notice, (dest, msg)))
			return
		
		reactor.callFromThread(self.botinst.notice, dest, msg)
		
		
	#callback to handle module returns
	#do we sanitize input? lol what input, result will be None if module doesn't return anything
	def moduledata(self, result):
		pass
	
	def moduleerr(self, e):
		print "error:", e #exception, or Failure thing
		
	def send_and_wait(self, sendfunc, sendargs, interestede, stope, timeout=10, sendkwargs={}):
		"""This is a super massively blocking method..."""
		start = time()
		while not self.botinst:
			if start + timeout > time(): 
				yield None
				return
			sleep(0.5)
		
		#yield events
		waitevent = WaitEvent(interestede, stope)
		#add wait events to dispatcher. ONLY MODIFY DISPATCHER IN REACTOR THREAD PLEASE.
		reactor.callFromThread(Dispatcher.addWaitEvent, self.settings.name, we)
		#send...
		sendfunc(*sendargs, **sendkwargs)
		# and now we play the waiting game...
		while not waitevent.done:
			try: item = results.get(timeout=0.5)
			except Empty: 
				if start + timeout > time(): 
					yield None
					return
			yield item
		return
		
