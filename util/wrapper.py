#botwrapper...
#This module does a few things. It holds a reference to the current botinstance
#it wraps actual botinst functions to limit the scope of what functions modules have access to within botinstance
#it also holds a queue for messages attempted to be sent while there is no current botinstance

from collections import deque
from twisted.internet import reactor

class BotWrapper:
	
	def __init__(self, network):
		self.network = network
		self.botinst = None
		self.outqueue = deque() #deque or Queue, whatever
	
	# TODO: if you want to do say, you need to somehow get the event... Otherwise you could easily have a say method on event that redirects to here
	# passing itself
	#def say(self, 
	
	def addbotinst(self, botinst):
		self.botinst = botinst
		# TODO: change this so that we are directly calling botinst's methods instead of wrapper
		# Do this so that there are no weird issues when calling callFromThread within the main reactor thread (which is when this will take place)
		for outbound in self.outqueue:
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
		
		reactor.callFromThread(self.botinst.notice, (dest, msg))
		
		
	#callback to handle module returns
	#do we sanitize input? lol what input, result will be None if module doesn't return anything
	def moduledata(self, result):
		pass
	
	def moduleerr(self, e):
		print "error:", e #exception, or Failure thing
		
		
		