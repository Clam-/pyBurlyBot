#waiteventexample.py

#example on how to send and then wait on events

from util import Mapping, Timers

def waitexample(event, bot):
	#
	pass

#mappings to methods
mappings = (Mapping(types=["privmsged"], command="waitexample", function=waitexample),)
