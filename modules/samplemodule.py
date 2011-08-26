#sample module
from re import compile as recompile
from util import Mapping
from util.db import DBQuery

class STUFF:
	#hold some things maybe settings or should a global settings object be passed in the method call?
	# atm if you want global settings you import Settings
	pass


def repeater(event, botinst):
	#do some things
	dest = event.channel
	botinst.msg(dest, "%s : %s" % (event.nick, event.msg))

#init should always be here to setup needed DB tables or objects or whatever
def init():
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	result = DBQuery("SELECT name FROM sqlite_master WHERE name='sample_table'")
	if result.error:
		#uh oh....
		print "What happened?: %s" % result.error
	else:
		#good
		if not result.rows:
			DBQuery('''
			create table sample_table(
			columnA,
			columnB
			);''')
		return True

#mappings to methods
mappings = (Mapping(types=["privmsg"], regex=recompile(r"\|.*"), function=repeater),)