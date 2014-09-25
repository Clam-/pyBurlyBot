def dummyfunc(event, botwrap):
	pass

#TODO: Should this be called "hook"? (with the variable name in modules called "hooks")
#	"hooks" seems kind of "low level" though...
class Mapping:
	def __init__(self, types=None, command=None, regex=None, function = dummyfunc, priority=10):
		# type = [list of strings], command=string, regex=compiledRegExobject, 
		#		function=a defined function should be expecting the following arguments:
		# def dummyfunc(event, botwrap):
		if not types: self.types = []
		else: self.types = types
		if command:
			if not self.types: 
				self.types = ["privmsged"]
		self.command = command
		self.regex = regex
		self.function = function
		self.priority = priority