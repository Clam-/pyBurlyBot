def dummyfunc(event, botinstance, dbqueue):
	pass

#TODO: Should this be called "hook"? (with the variable name in modules called "hooks")
#	"hooks" seems kind of "low level" though...
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