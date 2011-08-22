#users
from util import Mapping
from Queue import Queue

# class STATE:
	# enabled = True


def userupdate(event, botinst, db):
	#update last seen and such
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
	nick TEXT,
	host TEXT
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
	# if not exists:
	db.put(("SELECT name FROM sqlite_master WHERE name='user_nick_idx'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''CREATE INDEX user_nick_idx ON user(nick);''', results))
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating nick index... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
		return False
	return True

#mappings to methods
mappings = (Mapping(type=["privmsg"], function=userupdate),)