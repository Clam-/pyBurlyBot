#alias module
from util import Mapping, fetchone, argumentSplit, functionHelp, pastehelper
from sys import modules

REQUIRES = ("users",)
USERS_MODULE = None

def lookup_alias(qfunc, alias):
	result = qfunc('''SELECT user FROM alias WHERE alias = ?;''', (alias,), fetchone)
	#check rows...
	if not result:
		return None
	try:
		return result["user"]
	except IndexError:
		print "This shouldn't happen, invalid alias?"

def get_user(qfunc, nick):
	user = lookup_alias(qfunc, nick)
	if not user:
		user = USERS_MODULE.get_user(qfunc, nick)
	return user

def add_alias(qfunc, source, alias):
	qfunc('''INSERT OR REPLACE INTO alias (alias, user) VALUES (?,?);''', (alias, source))

def alias_list(qfunc, nick):
	result = qfunc('''SELECT alias FROM alias WHERE user = ?;''', (nick,))
	return filter(lambda x: x != nick, (row['alias'] for row in result) )
	
def group_list(qfunc, group):
	result = qfunc('''SELECT user FROM aliasgrp WHERE grp = ?;''', (group,))
	return [row['user'] for row in result]

def group_add(qfunc, group, nick):
	qfunc('''INSERT OR REPLACE INTO aliasgrp (grp, user) VALUES(?,?);''', (group, nick))

def group_check(qfunc, group, nick):
	return qfunc('''SELECT 1 FROM aliasgrp WHERE grp = ? AND user = ?;''', (group,nick), fetchone)
	

def alias(event, bot):
	""" alias [(source, ~group, ~del)] argument. If only argument is supplied, aliases for that argument are retrieved. 
	Otherwise if source is supplied, argument will become an alias of source. See addtional help for ~group and ~del.
	|alias ~group [groupname] argument: will add argument to groupname is groupname is provided, else will return all users in groupname.
	|alias ~del [(~group, groupname)] argument: will remove the user alias argument if supplied on it's own. ~group will remove the 
	entire group argument. If groupname is used will remove argument from group, in this case argument may be multiple entries.
	"""
	# API is similar to old bot
	arg1, arg2, arg3 = argumentSplit(event.argument, 3)
	if arg1 == "~group":
		if arg2 and arg3:
			# binding to a group
			nick = get_user(bot.dbQuery, arg2)
			if not nick:
				return bot.say("User/alias (%s) not found or seen." % arg2)
			if group_check(bot.dbQuery, arg2, arg3):
				return bot.say("User/alias (%s) is already a member of (%s)." % (arg3, arg2))
			group_add(bot.dbQuery, arg2, arg3)
			return bot.say("User/alias (%s) added to group (%s)." % (arg2, arg3))
				
		elif arg2:
			# querying a group
			members = group_list(bot.dbQuery, arg2)
			if members:
				msg = "Users in group (%s): %%s" % (arg2)
				return pastehelper(bot, msg, items=members, title="Members of (%s)" % arg2)
			else:
				return bot.say("Group not found: (%s)" % arg2)
		else:
			#show help for group
			return bot.say(functionHelp(alias, "~group"))
	elif arg1 == "~del":
		if arg2 and arg3:
			# do a delete on group
			if arg2 == "~group":
				#remove entire group
				group = bot.dbQuery('''SELECT grp FROM aliasgrp WHERE grp = ?;''', (arg3,), fetchone)
				if group:
					bot.dbQuery('''DELETE FROM aliasgrp WHERE grp = ?;''', (arg3,))
					return bot.say("Removed group (%s)" % arg3)
				else:
					return bot.say("Group (%s) not found." % arg3)
			else:
				# assume arg2 is a groupname to remove entry from
				group = bot.dbQuery('''SELECT grp FROM aliasgrp WHERE grp = ?;''', (arg2,), fetchone)
				if group:
					nick = get_user(bot.dbQuery, arg3)
					if not nick:
						return bot.say("User/alias (%s) not found." % arg3)
					if bot.dbQuery('''SELECT 1 FROM aliasgrp WHERE grp = ? AND user = ?;''', (arg2,nick), fetchone):
						bot.dbQuery('''DELETE FROM aliasgrp WHERE grp = ? AND user = ?;''', (arg2, nick))
						return bot.say("Removed (%s) from (%s)" % (nick, arg2))
					else:
						return bot.say("User/alias (%s) not found in group (%s)" % (nick, arg2))
				else:
					return bot.say("Group (%s) not found." % arg2)
		elif arg2:
			# single alias delete
			origin = lookup_alias(bot.dbQuery, arg1)
			if origin:
				bot.dbQuery('''DELETE FROM alias WHERE alias = ?;''', (arg2,))
				return bot.say("Alias (%s) for (%s) removed." % (arg1, origin))
			else:
				return bot.say("Alias (%s) not found." % arg2)
		else:
			# show help for del
			return bot.say(functionHelp(alias, "~del"))
	elif arg1 and arg2:
		#binding a new alias
		target = lookup_alias(bot.dbQuery, arg2) # check target
		if target:
			#alias already in use by nnick
			return bot.say("Alias already in use by (%s)" % target)
		# check if target is an existing/seen user.
		# in this case we are going to remove target user and execute all observers to user's rename plans.
		target = USERS_MODULE._get_username(bot.dbQuery, arg2)
		
		source = lookup_alias(bot.dbQuery, arg1)
		if not source:
			#look for user
			source = USERS_MODULE._get_username(bot.dbQuery, arg1)
			if source:
				if target: USERS_MODULE._rename_user(bot.network, target, source)
				add_alias(bot.dbQuery, source, source) # add origin mapping so that origins can't get aliased
				add_alias(bot.dbQuery, arg1, arg2)
				# find all groups that alias is a part of, and change membership to use "user" (source)
				bot.dbQuery('''UPDATE aliasgrp SET user=? WHERE user = ?;''', (source, arg2))
				return bot.say("Added (%s) to (%s)" % (arg2, arg1))
			else:
				return bot.say("(%s) not seen before." % arg1)
		else:
			if target: USERS_MODULE._rename_user(bot.network, target, source)
			add_alias(bot.dbQuery, source, arg2)
			return bot.say("Added (%s) to (%s)" % (arg2, source))
		
	elif arg1:
		#querying an alias
		nick = lookup_alias(bot.dbQuery, arg1)
		if nick:
			aliases = alias_list(bot.dbQuery, nick)
			msg = "Aliases for (%s): %%s" % arg1
			return pastehelper(bot, msg, items=aliases, title=msg)
		else:
			# unknown alias
			return bot.say("No aliases for (%s)" % arg1)
		
	# if none of the above, show help	
	bot.say(functionHelp(alias))
	return

#init should always be here to setup needed DB tables or objects or whatever
def init(bot):
	global USERS_MODULE # oh nooooooooooooooooo
	bot.dbCheckCreateTable("alias", 
		'''CREATE TABLE alias(
			alias TEXT PRIMARY KEY COLLATE NOCASE,
			user TEXT COLLATE NOCASE
		);''')
	bot.dbCheckCreateTable("aliasgrp", 
		'''CREATE TABLE aliasgrp(
			grp TEXT COLLATE NOCASE,
			user TEXT COLLATE NOCASE
		);''')
	#index alias column
	#Unique does this for us
	#but should index nick column so can do fast "get all alias for nick" queries...
	#	Consider going back to using integer IDs for this? I dunno if indexing integers is faster than TEXT in SQLite
	# if not exists:
	bot.dbCheckCreateTable("alias_user_idx", '''CREATE INDEX alias_user_idx ON alias(user);''')
	bot.dbCheckCreateTable("alias_group_idx", '''CREATE INDEX alias_group_idx ON aliasgrp(grp,user);''')
	
	# cache user module.
	# NOTE: you should only call getModule in init() if you have preloaded it first using "REQUIRES"
	USERS_MODULE = bot.getModule("users")
	# add backreference to alias module for fast lookup
	# this probably shouldn't normally be done.
	USERS_MODULE.ALIAS_MODULE = modules[__name__]
	return True

#mappings to methods
mappings = (Mapping(command="alias", function=alias),)
