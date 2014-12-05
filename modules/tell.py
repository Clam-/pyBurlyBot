#tell module
from time import gmtime, localtime, mktime
from calendar import timegm # silly python... I just want UTC seconds
from collections import deque

from util import Mapping, argumentSplit, functionHelp, distance_of_time_in_words, fetchone, pastehelper, stringlist
# added dependency on user module only for speed. Means can keep reference to user module without having
# to dive in to the reactor twice? per message
# because of this I should do foreign key things but don't want to lock myself in to that just yet (bad@db)
REQUIRES = ("users",)
USERS_MODULE = None

#nick: <source> msg - time
TELLFORMAT = "{0}: <{1}> {2} - {3}"
#nick: I'll pass that on when target is around.
RPLFORMAT = "%s: I'll pass that on when %s %s around.%s%s"
UNKNOWN = " Don't know (%s)."
URSELF = " Use notepad for yourself."
#nick: I will remind target about that in timespec.
RPLREMINDFORMAT = "%s: I will remind %s about that %s.%s"
#TARGET, reminder from SOURCE: MSG - set TELLTIME, arrived TOLDTIME.
REMINDFORMAT = "{0}, reminder from {1}: {2} - set {3}, arrived {4}."

#parsedatetime stuff
from parsedatetime import Constants, Calendar
c = Constants()
c.BirthdayEpoch = 80

PARSER = Calendar(c)

MAX_REMIND_TIME = 31540000 # 1 year

def _generate_users(bot, s, nick, skipself=True):
	users = [] # user,called
	unknown = []
	targets = deque(s.split(","))
	hasself = False
	while targets:
		t = targets.popleft()
		u = USERS_MODULE.get_username(bot, t, nick)
		if u: 
			if skipself and u == nick: hasself = True
			else: users.append((u, t))
		else:
			l = [t]
			while not u and targets:
				l.append(targets.popleft())
				u = USERS_MODULE.get_username(bot, ",".join(l), nick)
			# at this point we either have u or ran out of deque, if latter, throw l[1:] back on queue
			if u: 
				if skipself and u == nick: hasself = True
				else: users.append((u,",".join(l)))
			else: 
				unknown.append(l[0])
				l = l[1:]
				l.reverse()
				targets.extendleft(l)
	return users, unknown, hasself

def deliver_tell(event, bot):
	# if alias module available use it
	user = None
	if bot.isModuleAvailable("alias"):
		# pretty convoluted but faster than fetching both modules every time
		# may return none if this event gets captured for a first time user before user module
		# also faster this way than making 2 db calls for USER_MODULE.get_username
		user = USERS_MODULE.ALIAS_MODULE.lookup_alias(bot.dbQuery, event.nick)
	if not user: user = event.nick
	toldtime = int(timegm(gmtime()))
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
				data = [event.nick, tell['source'], tell['msg'], distance_of_time_in_words(tell['telltime'], toldtime), 
				distance_of_time_in_words(tell['telltime'], suffix="late")]
				if collate: lines.append(REMINDFORMAT.format(*data))
				else: bot.say(REMINDFORMAT, strins=data, fcfs=True)
			else:
				data = [event.nick, tell['source'], tell['msg'], distance_of_time_in_words(tell['telltime'], toldtime)]
				if collate: lines.append(TELLFORMAT.format(*data))
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
	users, unknown, hasself = _generate_users(bot, target, USERS_MODULE.get_username(bot, event.nick))

	if not users:
		if hasself: return bot.say("Use notepad.")
		else: return bot.say("Sorry, don't know (%s)." % target)
	
	targets = []
	for user, target in users:
		#cmd user msg
		msg = "%s %s %s" % (event.command, target, msg)
		# TODO: do we do an alias lookup on event.nick also?
		bot.dbQuery('''INSERT INTO tell(user, telltime, source, msg) VALUES (?,?,?,?);''',
			(user, int(timegm(gmtime())), event.nick, msg))
		targets.append(target)
	# check if we need to warn about too many tell pastebin
	# https://github.com/Clam-/pyBurlyBot/issues/29 
	#~ n = bot.dbQuery('''SELECT COUNT(id) AS C FROM tell WHERE user = ? AND delivered = ? AND telltime < ?;''', (user, 0, time()), fetchone)['C']
	#~ if n > 3:
		#~ print "GUNNA WARNING"
	if len(users) > 1:
		bot.say(RPLFORMAT % (event.nick, stringlist(targets), "are", 
			UNKNOWN % stringlist(unknown) if unknown else "", URSELF if hasself else ""))
	else:
		bot.say(RPLFORMAT % (event.nick, stringlist(targets), "is",  
			UNKNOWN % stringlist(unknown) if unknown else "", URSELF if hasself else ""))
	
def remind(event, bot):
	""" remind target datespec msg. Will remind a user <target> about a message <msg> at datespec time. datespec can be relative (in) or calendar/day based (on), e.g. 'in 5 minutes"""
	target, dtime1, dtime2, msg = argumentSplit(event.argument, 4)
	if not target: return bot.say(bot.say(functionHelp(tell)))
	if dtime1 == "tomorrow":
		target, dtime1, msg = argumentSplit(event.argument, 3) # reparse is easiest way I guess... resolves #30 if need to readdress
		dtime2 == ""
	else:
		if not (dtime1 and dtime2): return bot.say("Need time to remind.")
	if not msg:
		return bot.say("Need something to remind (%s)" % target)
	
	origuser = USERS_MODULE.get_username(bot, event.nick)
	users, unknown, _ = _generate_users(bot, target, origuser, False)

	if not users:
		return bot.say("Sorry, don't know (%s)." % target)
	
	dtime = "%s %s" % (dtime1, dtime2)
	# user location aware destination times
	locmod = None
	goomod = None
	timelocale = False
	try:
		locmod = bot.getModule("location")
		goomod = bot.getModule("googleapi")
		timelocale = True
	except ConfigException: pass
		
	if locmod and goomod:
		t = timegm(gmtime())
		#borrowed from time.py
		loc = locmod.getlocation(bot.dbQuery, origuser)
		if not loc:
			t = localtime()
			timelocale = False
		else:
			tz = goomod.google_timezone(loc[1], loc[2], t)
			if not tz:
				t = localtime()
				timelocale = False
			else:
				t = gmtime(t + tz[2] + tz[3]) #[2] dst [3] timezone offset
	else:
		t = localtime()
	ntime, code = PARSER.parse(dtime, t)

	if code == 0:
		return bot.say("Don't know what time and/or day and/or date (%s) is." % dtime)
	if code == 1: # nuke hours minutes seconds if this is a date reminder so that we don't remind on some crazy hour
		ntime = list(ntime)
		ntime[3:6] = (0,0,0)
		ntime = tuple(ntime)
	# go on, change it. I dare you.
	if timelocale:
		t = timegm(t) - tz[2] - tz[3]
		ntime = timegm(ntime) - tz[2] - tz[3]
	else:
		t = mktime(t)
		ntime = mktime(ntime)

	if ntime < t or ntime > t+MAX_REMIND_TIME:
		return bot.say("Don't sass me with your back to the future reminds.")
	
	targets = []
	for user, target in users:
		bot.dbQuery('''INSERT INTO tell(user, telltime, remind, source, msg) VALUES (?,?,?,?,?);''',
			(user, int(ntime), 1, event.nick, msg))
		if user == USERS_MODULE.get_username(bot, event.nick): targets.append("you")
		else: targets.append(target)
	
	bot.say(RPLREMINDFORMAT % (event.nick, stringlist(targets), distance_of_time_in_words(ntime, t), UNKNOWN % stringlist(unknown) if unknown else ""))
		

def _user_rename(old, new):
	return (('''UPDATE tell SET user=? WHERE user=?;''', (new, old)),)
	
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
