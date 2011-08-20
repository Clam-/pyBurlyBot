
def dummyfunc(event):
	pass

class Mapping:
	def __init__(self, type=None, command=None, regex=None, function = dummyfunc):
		# type = [list of strings], command=string, regex=compiledRegExobject, function=a defined function that has the signature:
		#	def dummyfunc(event, botinstance, dbqueue):
		self.type = type
		self.command = command
		self.regex = regex
		self.function = function