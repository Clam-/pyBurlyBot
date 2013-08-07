#users

#BROKEN: awaiting new msg hooks

#twisted
from twisted.python import log
#bbm
from util import Mapping
from util.db import DBQuery
#python
from time import time
#helpers
from util import distance_of_time_in_words

def _user_update(event, nick=None):
	#check if exists, then update
	if not nick: nick = event.nick
	result = DBQuery('''INSERT OR REPLACE INTO user (nick, host, lastseen, seenwhere) VALUES(?,?,?,?);''',
		(nick, event.hostmask, int(time()), event.channel))
	if result.error:
		print "What happened?: %s" % result.error

def user_update(event, bot):
	#check is alias is loaded and available
	if bot.isModuleAvailable("alias"):
		# TODO: use some alias module methods using bot.getModule("alias").method()
		result = DBQuery('''SELECT nick FROM alias WHERE alias = ?;''', (event.nick,))
		if not result.error:
			#check rows...
			if not result.rows:
				#if no results:
				_user_update(event)
			else:
				nick = result.rows[0]["nick"]
				_user_update(event, nick)
		else:
			print "What happened?: %s" % result.error
	else:
		#alias not loaded
		_user_update(event)
	return

def _user_seen(event, nick=None):
	#check if exists, then update
	if not nick: nick = event.input
	result = DBQuery('''SELECT lastseen, seenwhere FROM user WHERE nick = ?;''', (nick, ))
	if result.error:
		print "What happened?: %s" % result.error
		return None
	return result.rows[0] if result.rows else None

def user_seen(event, bot):
	if not event.input:
		print "what"
		return
	
	seen = None
	if bot.isModuleAvailable("alias"):
		# TODO: use some alias module methods using bot.getModule("alias").method()
		result = DBQuery('''SELECT nick FROM alias WHERE alias = ?;''', (event.input,))
		if result.error:
			print "What happened?: %s" % result.error
			return
		#check rows...
		if not result.rows:
			#if no results:
			seen = _user_seen(event)
		else:
			nick = result.rows[0]["nick"]
			seen = _user_seen(event, nick)

	else:
		#alias not loaded
		seen = _user_seen(event)
	if not seen:
		bot.msg(event.channel, "lol dunno.")
	else:
		bot.msg(event.channel, "%s - %s" % (distance_of_time_in_words(seen["lastseen"]), seen["seenwhere"]))
	return
	
#init should always be here to setup needed DB tables or objects or whatever
def init():
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	query = DBQuery()
	query.query('''SELECT name FROM sqlite_master WHERE name='user';''')
	if query.error:
		#uh oh....
		print "What happened?: %s" % query.error
		return False

	#primary key should be made up of server+nick
	if not query.rows:
		query.query('''
			create table user(
			nick TEXT PRIMARY KEY,
			host TEXT,
			lastseen INTEGER,
			seenwhere TEXT
			);''')
		# should probably make sure this returns valid
		if query.error:
			print "Error creating table... %s" % query.error
			return False

	
	#should probably index nick column
	#unique does this for us
	#but should probably index lastseen so can ez-tells:
	# if not exists:
	query.query('''SELECT name FROM sqlite_master WHERE name='user_lastseen_idx';''')
	if query.error:
		#uh oh
		print "What happened?: %s" % query.error
		return False

	if not query.rows:
		query.query('''CREATE INDEX user_lastseen_idx ON user(lastseen);''')
		if query.error:
			print "Error creating lastseen index... %s" % query.error
			return False

	return True

#mappings to methods
mappings = (Mapping(types=["privmsged"], function=user_update), Mapping(types=["privmsged"], command="seen", function=user_seen))
