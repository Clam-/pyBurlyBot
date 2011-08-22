#alias module
from re import compile as recompile
from util import Mapping
from Queue import Queue
from settings import Settings

def alias(event, botinst, db):
	#do some alias things, like add, remove, and displaying
	pass

#init should always be here to setup needed DB tables or objects or whatever
def init(db):
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	#require that user is loaded already:
	if "users" not in Settings.moduledict:
		print "ERROR LOADING ALIAS: REQUIREMENT OF users MODULE NOT MET"
		return False
	
	results = Queue()
	db.put(("SELECT name FROM sqlite_master WHERE name='alias'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''
create table alias(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	alias TEXT UNIQUE,
	user INTEGER
);''', results))
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating table... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
	
	#index alias column
	#Unique does this for us
	return True

#mappings to methods
mappings = (Mapping(type=["privmsg"], command="alias", function=alias),)