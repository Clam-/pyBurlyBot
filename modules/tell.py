#tell module
from time import time, mktime

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
#nick: I will remind target about that in timespec.
RPLREMINDFORMAT = "%s: I will remind %s about that in %s."
#TARGET, reminder from SOURCE: MSG - set TELLTIME, arrived TOLDTIME.
REMINDFORMAT = "%s, reminder from %s: %s - set %s, arrived %s."

#parsedatetime stuff
from parsedatetime import Constants, Calendar
c = Constants()
c.BirthdayEpoch = 80

PARSER = Calendar(c)

YEARLIMIT = 31540000

def deliver_tell(event, bot):
	# if alias module available use it
	user = None
	if bot.isModuleAvailable("alias"):
		# pretty convoluted but faster than fetching both modules every time
		# may return none if this event gets captured for a first time user before user module
		# also faster this way than making 2 db calls for USER_MODULE.get_username
		user = USERS_MODULE.ALIAS_MODULE.lookup_alias(bot.dbQuery, event.nick)
	if not user: user = event.nick
	toldtime = int(time())
	tells = bot.dbQuery('''SELECT id,source,telltime,remind,msg FROM tell WHERE user=? AND delivered=0 AND telltime<? ORDER BY telltime;''', 
		(user,toldtime))
	if tells:
		collate = False
		lines = None
		if len(tells) > 3: 
			collate = True
			lines = []
		for tell in tells:
			if tell['remind']:
				data = (event.nick, tell['source'], tell['msg'], distance_of_time_in_words(tell['telltime'], toldtime), 
				distance_of_time_in_words(tell['telltime'], suffix="late"))
				if collate: lines.append(REMINDFORMAT % data)
				else: bot.say(REMINDFORMAT, strins=data, fcfs=True)
			else:
				data = (event.nick, tell['source'], tell['msg'], distance_of_time_in_words(tell['telltime'], toldtime))
				if collate: lines.append(TELLFORMAT % data)
				else: bot.say(TELLFORMAT, strins=data, fcfs=True)
			#TODO: change this to do a bulk update somehow?
			bot.dbQuery('''UPDATE tell SET delivered=1,toldtime=? WHERE id=?;''', (toldtime, tell['id']))
		if collate:
			msg = "Tells/reminds for (%s)" % event.nick
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
	
def remind(event, bot):
	""" remind target datespec msg. Will remind a user <target> about a message <msg> at datespec time. datespec can be relative (in) or calendar/day based (on), e.g. 'in 5 minutes"""
	target, dtime1, dtime2, msg = argumentSplit(event.argument, 4)
	if not target: return bot.say(bot.say(functionHelp(tell)))
	if not (dtime1 and dtime2): return bot.say("Need time to remind.")
	if not msg:
		return bot.say("Need something to remind (%s)" % target)
	# TODO: check if tell self
	user = USERS_MODULE.get_username(bot, target)
	if not user:
		return bot.say("Sorry, don't know (%s)." % target)
	
	#TODO: can optimize this probably by getting current time once, using it as a sourcetime to parse
	#	and then using it later for the time comparisons...
	dtime = "%s %s" % (dtime1, dtime2)
	tspec, code = PARSER.parse(dtime)
	if code == 0:
		return bot.say("Don't know what time/day/date (%s) is." % dtime)
	ntime = mktime(tspec)
	if ntime < time() or ntime > time()+YEARLIMIT:
		return bot.say("Don't sass me with your back to the future reminds.")
		
	# TODO: do we do an alias lookup on event.nick also?
	bot.dbQuery('''INSERT INTO tell(user, telltime, remind, source, msg) VALUES (?,?,?,?,?);''',
		(user, int(ntime), 1, event.nick, msg))
	bot.say(RPLREMINDFORMAT % (event.nick, target, distance_of_time_in_words(ntime)))
		

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
			remind INTEGER DEFAULT 0,
			source TEXT,
			msg TEXT
		);''')
	# I am bad at indexes.
	bot.dbCheckCreateTable("tell_deliv_idx", '''CREATE INDEX tell_deliv_idx ON tell(user, delivered, telltime);''')
	
	# cache user module.
	# NOTE: you should only call getModule in init() if you have preloaded it first using "REQUIRES"
	USERS_MODULE = bot.getModule("users")
	# Modules storing "users" in their own tables should register to be notified when a username is changed (by the alias module)
	USERS_MODULE.REGISTER_UPDATE(bot.network, _user_rename)
	return True

mappings = (Mapping(types=["privmsged"], function=deliver_tell),
	Mapping(command="tell", function=tell), Mapping(command="remind", function=remind),)
