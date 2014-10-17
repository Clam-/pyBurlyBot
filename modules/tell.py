#tell module
from time import time

from util import Mapping, argumentSplit, functionHelp, distance_of_time_in_words
# added dependency on user module only for speed. Means can keep reference to user module without having
# to dive in to the reactor twice? per message
# because of this I should do foreign key things but don't want to lock myself in to that just yet (bad@db)
REQUIRES = ("users",)
USERS_MODULE = None

#nick: <source> msg - time
TELLFORMAT = "%s: <%s> %s - %s"
#nick: I'll pass that on when target is around.
RPLFORMAT = "%s: I'll pass that on when %s is around."

def deliver_tell(event, bot):
	# if alias module available use it
	user = None
	if bot.isModuleAvailable("alias"):
		# pretty convoluted but faster than fetching both modules every time
		# may return none if this event gets captured for a first time user before user module
		user = USERS_MODULE.ALIAS_MODULE.lookup_alias(bot.dbQuery, event.nick)
	if not user: user = event.nick
	
	tells = bot.dbQuery('''SELECT id,source,telltime,msg FROM tell WHERE user=? AND delivered=0 ORDER BY telltime;''', (user,))
	if tells:
		toldtime = int(time())
		collate = False
		lines = None
		if len(tells) > 3: 
			collate = True
			lines = []
		for tell in tells:
			data = (event.nick, tell['source'], tell['msg'], distance_of_time_in_words(tell['telltime'], toldtime))
			if collate: lines.append(TELLFORMAT % data)
			else: bot.say(TELLFORMAT, strins=data, fcfs=True)
			#TODO: change this to do a bulk update somehow?
			bot.dbQuery('''UPDATE tell SET delivered=1,toldtime=? WHERE id=?;''', (toldtime, tell['id']))
		if collate:
			msg = "Tells for (%s)" % event.nick
			pastehelper(bot, msg, items=lines, title=msg)
			

def tell(event, bot):
	""" tell target msg. Will tell a user <target> a message <msg>."""
	target, msg = argumentSplit(event.argument, 2)
	if not target: return bot.say(bot.say(functionHelp(tell)))
	if not msg:
		return bot.say("Need something to tell (%s)" % target)
	# TODO: check if tell self
	user = USERS_MODULE.get_username(bot, target)
	if not user:
		return bot.say("Sorry, don't know (%s)." % target)
	
	#cmd user msg
	msg = "%s %s %s" % (event.command, target, msg)
	# TODO: do we do an alias lookup on event.nick also?
	bot.dbQuery('''INSERT INTO tell(user, telltime, source, msg) VALUES (?,?,?,?);''',
		(user, int(time()), event.nick, msg))
	bot.say(RPLFORMAT % (event.nick, target))

def _user_rename(old, new):
	return ('''UPDATE tell SET user=? WHERE user=?;''', (new, old))
	
def init(bot):
	global USERS_MODULE # oh nooooooooooooooooo
	bot.dbCheckCreateTable("tell", 
		'''CREATE TABLE tell(
			id INTEGER PRIMARY KEY,
			delivered INTEGER DEFAULT 0,
			user TEXT COLLATE NOCASE,
			telltime INTEGER,
			toldtime INTEGER,
			source TEXT,
			msg TEXT
		);''')
	# I am bad at indexes.
	bot.dbCheckCreateTable("tell_deliv_idx", '''CREATE INDEX tell_deliv_idx ON tell(user, delivered, toldtime);''')
	
	# cache user module.
	# NOTE: you should only call getModule in init() if you have preloaded it first using "REQUIRES"
	USERS_MODULE = bot.getModule("users")
	# Modules storing "users" in their own tables should register to be notified when a username is changed (by the alias module)
	USERS_MODULE.REGISTER_UPDATE(bot.network, _user_rename)
	return True

mappings = (Mapping(types=["privmsged"], function=deliver_tell),
	Mapping(command="tell", function=tell),)
