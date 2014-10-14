#users
from util import Mapping, distance_of_time_in_words, fetchone, pastehelper, ADDONS

ALIAS_MODULE = None

OPTIONS = {
	"hidden" : (list, "Channels in this list will not be shown in seen requests.", []),
}

SEENMSGWSOURCE = 'I last saw %s %s on %s. "%s"'
SEENMSG = 'I last saw %s %s.'

def _user_update(qfunc, event, nick=None):
	#check if exists, then update
	if not nick: nick = event.nick
	qfunc('''INSERT OR REPLACE INTO user (user, host, lastseen, seenwhere, lastmsg) VALUES(?,?,?,?,?);''',
		(nick, event.hostmask, int(event.time), event.target, event.msg))

def user_update(event, bot):
	#check is alias is loaded and available
	# this method gets called on the reactor so it may cause many context switches :(
	if bot.isModuleAvailable("alias"):
		_user_update(bot.dbQuery, event, ALIAS_MODULE.get_nick(bot.dbQuery, event.nick))
	else:
		#alias not loaded
		_user_update(bot.dbQuery, event)
	return

def get_user(qfunc, nick):
	user = qfunc('''SELECT user FROM user WHERE user = ?;''', (nick,), func=fetchone)
	if user: return user['user']
	return user

def _user_seen(qfunc, nick):
	return qfunc('''SELECT lastseen, seenwhere, lastmsg FROM user WHERE user = ?;''', (nick, ), fetchone)

def user_seen(event, bot):
	target = event.argument
	if not target:
		return bot.say("Seen who?")
	
	hidden = bot.getOption("hidden", module="users")
	
	if bot.isModuleAvailable("alias"):
		# do magic for group
		group = ALIAS_MODULE.group_list(bot.dbQuery, target)
		if group:
			msgs = []
			for member in group:
				seen = _user_seen(bot.dbQuery, member)
				if seen['seenwhere'] in hidden:
					msgs.append(SEENMSG % (target, distance_of_time_in_words(seen['lastseen']) ))
				else:
					msgs.append(SEENMSGWSOURCE % (target, distance_of_time_in_words(seen['lastseen']),
						seen['seenwhere'], seen['lastmsg']))
			if len(group) > 3:
				try:
					return "%s, see %s" % (event.nick, ADDONS.paste("\n".join(msgs), title="Seen %s" % target))
				except AttributeError:
					return bot.say("Too many users and no paste available.")
			else:
				first = True
				for msg in msgs: 
					if first: bot.say("%s, %s" % (event.nick, msg))
					else: bot.say(msg)
					first = False
				return
		
		# not group, look for alias:
		nick = ALIAS_MODULE.get_nick(bot.dbQuery, target)
		seen = _user_seen(bot.dbQuery, nick if nick else target)
	else:
		seen = _user_seen(target)
	
	if not seen:
		bot.say("%s, lol dunno." % event.nick)
	else:
		if seen['seenwhere'] in hidden:
			bot.say("%s, %s" % (event.nick, SEENMSG % (target, distance_of_time_in_words(seen['lastseen'])) ))
		else:
			bot.say("%s, %s" % (event.nick, SEENMSGWSOURCE % (target, distance_of_time_in_words(seen['lastseen']),
				seen['seenwhere'], seen['lastmsg'])))
	return
	
#init should always be here to setup needed DB tables or objects or whatever
def init(bot):
	"""Do startup module things. This just checks if table exists. If not, creates it."""
	bot.dbCheckCreateTable('user',
		'''CREATE TABLE user(
			user TEXT PRIMARY KEY,
			host TEXT,
			lastseen INTEGER,
			seenwhere TEXT,
			lastmsg TEXT
		);''')

	#should probably index nick column
	#unique does this for us
	#but should probably index lastseen so can ez-tells:
	# if not exists:
	bot.dbCheckCreateTable("user_lastseen_idx", '''CREATE INDEX user_lastseen_idx ON user(lastseen);''')
	return True

#mappings to methods
mappings = (Mapping(types=["privmsged"], function=user_update), Mapping(command="seen", function=user_seen))
