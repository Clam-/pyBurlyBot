from settings import Settings
from state import State
from timer import Timers

#should we put db things here? so in module can go "from util import Settings, DBQuery, checkcreatetable, etc"

#probably should move the following into mapping.py or something
# and keep this just as a "import 'reference/insertion' point" lol for lack of better word
# Yeah, and this should only contain "user friendly" things... For example things that should be accessable to modules.
# anything else (like DBaccess or whatever) should be imported via it's full domain.
def dummyfunc(event, botinstance, dbqueue):
	pass

class Mapping:
	def __init__(self, types=[], command=None, regex=None, function = dummyfunc, priority=10):
		# type = [list of strings], command=string, regex=compiledRegExobject, 
		#		function=a defined function should be expecting the following arguments:
		# def dummyfunc(event, botinstance, dbqueue):
		self.types = types
		self.command = command
		self.regex = regex
		self.function = function
		self.priority = priority