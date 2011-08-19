#sample module
from re import compile as recompile
from util import Mapping

class STUFF:
	#hold some things maybe settings or should a global settings object be passed in the method call?
	pass


#Need to work out a signature that can capture all types of messages, maybe encapsulate the data in a Message object, that has it's own attributes populated
def repeater(event, botinst, db):
	#do some things
	#if we do this in a thread, I wonder if STUFF will be accessable for like module-level options
	#instead of a thread, we might be able to make a call to this with a twisted defer... but that might be sort of the same thing, need to check
	#return the message as in, need to work out proper return signature
	dest = event.channel
	botinst.msg(dest, "%s : %s" % (event.user, event.msg))
	#return (type, {"dest" : dest, "msg" : "%s : %s" % (data["user"], data["msg"])}) #source is actually dest, whatever

#init should always be here to setup needed DB tables or objects or whatever
def init(db):
	"""Do startup module things"""
	return True

#mappings to methods
mappings = (Mapping(type=["ALL"], regex=recompile(r"\|.*"), function=repeater),)