# utils for modules to import
from timer import Timers
from timehelpers import distance_of_time_in_words

from mapping import Mapping

from db import DBQuery, dbCheckCreateTable

# Simple command parse and return (command, argument)
# split arguments in to [nargs] number of elements 
# only if number of arguments would equal nargs, otherwise return None argument
def commandSplit(s, nargs=1):
	command = ""
	if s:
		command = s.split(" ", 1)
		if len(command) > 1:
			if nargs > 1:
				a = command[1].split(" ", nargs)
				if len(a) != nargs:
					return (command[0], None)
				else:
					return (command[0], a)
			else:
				return command
		else:
			return command[0], None
	return (None, None)

# like commandSplit, this is only for splitting arguments up
def argumentSplit(s, nargs):
	if s:
		a = s.split(" ", nargs)
		if len(a) != nargs:
			return ()
		else:
			return a
	else:
		return ()