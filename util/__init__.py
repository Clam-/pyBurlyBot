
def dummyfunc(event, botinstance, dbqueue):
	pass

class Mapping:
	def __init__(self, type=None, command=None, regex=None, function = dummyfunc):
		# type = [list of strings], command=string, regex=compiledRegExobject, 
		#		function=a defined function should be expecting the following arguments:
		# def dummyfunc(event, botinstance, dbqueue):
		self.type = type
		self.command = command
		self.regex = regex
		self.function = function