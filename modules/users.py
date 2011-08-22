#users
from util import Mapping
from Queue import Queue

# class STATE:
	# enabled = True


def userupdate(event, botinst, db):
	#check if exists, then update
	pass

#init should always be here to setup needed DB tables or objects or whatever
def init(db):
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	results = Queue()
	db.put(("SELECT name FROM sqlite_master WHERE name='user'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''
create table user(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	nick TEXT UNIQUE,
	host TEXT,
	lastseen DATE
);''', results))
			# should probably make sure this returns valid
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating table... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
		return False
	
	#should probably index nick column
	#unique does this for us
	return True

#mappings to methods
mappings = (Mapping(type=["privmsg"], function=userupdate),)