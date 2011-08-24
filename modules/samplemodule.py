#sample module
from re import compile as recompile
from util import Mapping
from Queue import Queue

class STUFF:
	#hold some things maybe settings or should a global settings object be passed in the method call?
	# atm if you want global settings you import Settings
	pass


def repeater(event, botinst, db):
	#do some things
	dest = event.channel
	botinst.msg(dest, "%s : %s" % (event.nick, event.msg))

#init should always be here to setup needed DB tables or objects or whatever
def init(db):
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	results = Queue()
	db.put(("SELECT name FROM sqlite_master WHERE name='sample_table'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''
	create table sample_table(
		columnA,
		columnB
		);''', results))
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
	return True

#mappings to methods
mappings = (Mapping(types=["privmsg"], regex=recompile(r"\|.*"), function=repeater),)