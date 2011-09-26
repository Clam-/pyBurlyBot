#users
#twisted
from twisted.python import log
#bbm
from util import Mapping, Settings
from util.db import DBQuery
#python
from time import time
#lolhelpers
from webhelpers.date import distance_of_time_in_words

def _user_update(event, nick=None):
	#check if exists, then update
	if not nick: nick = event.nick
	result = DBQuery('''INSERT OR REPLACE INTO user (nick, host, lastseen, seenwhere) VALUES(?,?,?,?);''',
		(nick, event.hostmask, int(time()), event.channel))
	if result.error:
		print "What happened?: %s" % result.error

def user_update(event, botinst):
	#check is alias is loaded
	#check if it's allowed on server, and then check if it's actually loaded in moduledict
	# FIXME checking allowed modules, server method?
	# ("alias" in Settings.servers[botinst.network].allowmodules)
	if ("alias" in Settings.moduledict):
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

def user_seen(event, botinst):
	if not event.input:
		botinst.msg(event.channel, "lol wut")
		return
	
	seen = None
	# FIXME checking allowed modules, server method?
	# ("alias" in Settings.servers[botinst.network].modules)
	if ("alias" in Settings.moduledict):
		# TODO This should use alias module methods. This should happen in all places in this module that do alias things.
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
		botinst.msg(event.channel, "lol dunno.")
	else:
		botinst.msg(event.channel, "%s - %s" % (distance_of_time_in_words(int(seen["lastseen"]), int(time())), seen["seenwhere"]))
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
mappings = (Mapping(types=["privmsg"], function=user_update), Mapping(types=["privmsg"], command="seen", function=user_seen))
