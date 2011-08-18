#sample module
from re import compile as recompile

class STUFF:
	#hold some things maybe settings or should a global settings object be passed in the method call?
	pass


#Need to work out a signature that can capture all types of messages, maybe encapsulate the data in a Message object, that has it's own attributes populated
def repeater(type, data):
	#do some things
	#if we do this in a thread, I wonder if STUFF will be accessable for like module-level options
	#instead of a thread, we might be able to make a call to this with a twisted defer... but that might be sort of the same thing, need to check
	print "WOAH GOT DISPATCH??"
	#return the message as in, need to work out proper return signature
	dest = data["channel"]
	return (type, {"dest" : dest, "msg" : "%s : %s" % (data["user"], data["msg"])}) #source is actually dest, whatever




#TYPE(s), regex, method
mapping = (
	(["ALL"], recompile(r"\|.*"), repeater)
)