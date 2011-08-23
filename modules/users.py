#users

from twisted.python import log
from util import Mapping
from Queue import Queue
from time import time
from settings import Settings
from webhelpers.date import distance_of_time_in_words

def _userupdate(event, db, results, nick=None):
	#check if exists, then update
	if not nick: nick = event.nick
	db.put(('''INSERT OR REPLACE INTO user (nick, host, lastseen, seenwhere) VALUES(?,?,?,?);''', results, (nick, event.hostmask, int(time()), event.channel)))
	result = results.get()
	if result[0] != "SUCCESS":
		print "What happened?: %s" % result[1]

def userupdate(event, botinst, db):
	results = Queue()
	#check is alias is loaded
	#check if it's allowed on server, and then check if it's actually loaded in moduledict
	if ("alias" in Settings.servers[botinst.servername].modules) and ("alias" in Settings.moduledict):
		db.put(('''SELECT nick FROM alias WHERE alias = ?;''', results, (event.nick,)))
		result = results.get()
		if result[0] == "SUCCESS":
			#check rows...
			if not result[1]:
				#if no results:
				_userupdate(event, db, results)
			else:
				nick = result[1][0]["nick"]
				_userupdate(event, db, results, nick)
		else:
			print "What happened?: %s" % result[1]
	else:
		#alias not loaded
		_userupdate(event, db, results)
	return

def _userseen(event, db, results, nick=None):
	#check if exists, then update
	if not nick: nick = event.input
	db.put(('''SELECT lastseen, seenwhere FROM user WHERE nick = ?;''', results, (nick, )))
	result = results.get()
	if result[0] != "SUCCESS":
		print "What happened?: %s" % result[1]
	else:
		if not len(result[1]) > 0:
			return None
		else:
			return result[1][0]

def userseen(event, botinst, db):
	if not event.input:
		botinst.msg(event.channel, "lol wut")
		return
	
	results = Queue()
	seen = None
	if ("alias" in Settings.servers[botinst.servername].modules) and ("alias" in Settings.moduledict):
		db.put(('''SELECT nick FROM alias WHERE alias = ?;''', results, (event.input,)))
		result = results.get()
		if result[0] == "SUCCESS":
			#check rows...
			if not result[1]:
				#if no results:
				seen = _userseen(event, db, results)
			else:
				nick = result[1][0]["nick"]
				seen = _userseen(event, db, results, nick)
		else:
			print "What happened?: %s" % result[1]
			return
	else:
		#alias not loaded
		seen = _userseen(event, db, results)
	if not seen:
		botinst.msg(event.channel, "lol dunno.")
	else:
		botinst.msg(event.channel, "%s - %s" % (distance_of_time_in_words(int(seen["lastseen"]), int(time())), seen["seenwhere"]))
	return
	
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
	nick TEXT PRIMARY KEY,
	host TEXT,
	lastseen INTEGER,
	seenwhere TEXT
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
	#but should probably index lastseen so can ez-tells:
	# if not exists:
	db.put(("SELECT name FROM sqlite_master WHERE name='user_lastseen_idx'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''CREATE INDEX user_lastseen_idx ON user(lastseen);''', results))
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating lastseen index... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
		return False
	return True

#mappings to methods
mappings = (Mapping(type=["privmsg"], function=userupdate),Mapping(type=["privmsg"], command="seen", function=userseen))