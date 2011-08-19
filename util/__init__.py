
def dummyfunc(event):
	pass

class Mapping:
	def __init__(self, type=None, command=None, regex=None, function = dummyfunc):
		self.type = type
		self.command = command
		self.regex = regex
		self.function = function