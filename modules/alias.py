#alias module
from util import Mapping, Settings
from util.db import DBQuery

def get_nick(alias):
	result = DBQuery('''SELECT nick FROM alias WHERE alias = ?;''', (alias,))
	if result.error:
		print "Something very wrong happened: %s" % result.error
		return None
	#check rows...
	if not result.rows:
		#if no results:
		return None
	else:
		return result.rows[0]["nick"]

def add_alias(nick, alias):
	result = DBQuery('''INSERT INTO alias (alias, nick) VALUES (?,?);''', (alias, nick))
	if result.error:
		print "Something wrong with aliasadd %s" % result.error
		return False
	return True

def _list_alias(nick):
	aliases = []
	result = DBQuery('''SELECT alias FROM alias WHERE nick = ?;''', (nick,))
	if result.error:
		print "Something wrong with aliaslist %s" % result.error
	else:
		for row in result.rows:
			aliases.append(row['alias'])
	return aliases

def alias(event, botinst):
	# parse input "add" "del", etc
	#lol Griff can fix all this up. Debug onry
	query = DBQuery()
	#lol steal codes
	command = ""
	if event.input:
		command = event.input.split(" ", 1)
		if len(command) > 1:
			command, input = command
		else:
			command, input = command[0], None
	if command == "add":
		if not input:
			botinst.msg(event.channel, "Need source and dest.")
			return
		things = input.split(" ", 1)
		if len(things) >2:
			botinst.msg(event.channel, "Need source and dest.")
			return
		source, new = things
		#check if source is alias
		nnick = get_nick(new)
		if nnick:
			#alias already in use by nnick
			botinst.msg(event.channel, "Nick already in use by %s" % nnick)
			return
		nick = get_nick(source)
		if not nick:
			#look for user
			query.query('''SELECT 1 FROM user WHERE nick = ?;''', (source,))
			if query.error:
				print "Something really bad aaa %s" % query.error
				return
			if query.rows:
				if add_alias(source, new):
					botinst.msg(event.channel, "Added %s to %s" % (new, source))
			else:
				botinst.msg(event.channel, "%s not seen before." % source)
				return
			
		else:
			#add new to nick-source
			if add_alias(nick, new):
				botinst.msg(event.channel, "Added %s to %s" % (new, nick))
	elif command == "del":
		if not input:
			botinst.msg(event.channel, "Need alias to remove")
			return
		#just blindly delete?
		#well I guess check if exists at least
		query.query('''SELECT 1 FROM alias WHERE alias = ?;''', (input,))
		if query.error:
			print "bad happen bbb %s" % query.error
			return
		if not query.rows:
			botinst.msg(event.channel, "%s alias not found" % input)
		
		#exists
		#okay to try delete
		query.query('''DELETE FROM alias WHERE alias = ?;''', (input,))
		if query.error:
			botinst.msg(event.channel, "Remove of alias failed: %s" % query.error)
	
	else:
		#show aliases:
		source = event.input
		if not source: source = event.nick
		#look for specific user
		nick = get_nick(source)
		if nick:
			aliases = _list_alias(nick)
			botinst.msg(event.channel, "Aliases for %s: %s" % (nick, ", ".join(aliases)))
			return
		else:
			#check for actual nick, actually, just blind it...
			# can do fancy later
			aliases = _list_alias(source)
			botinst.msg(event.channel, "Aliases for %s: %s" % (source, ", ".join(aliases)))
	return

#init should always be here to setup needed DB tables or objects or whatever
def init():
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	#require that user is loaded already:
	if "users" not in Settings.moduledict:
		print "ERROR LOADING ALIAS: REQUIREMENT OF users MODULE NOT MET"
		return False
	
	query = DBQuery('''SELECT name FROM sqlite_master WHERE name='alias';''')
	if query.error:
		#uh oh....
		print "What happened?: %s" % query.error
		return False

	#primary key should be made up of server+alias
	if not query.rows:
		query.query('''
			create table alias(
			alias TEXT PRIMARY KEY,
			nick TEXT
			);''')

		if query.error:
			print "Error creating table... %s" % query.error
			return False

	
	#index alias column
	#Unique does this for us
	#but should index nick column so can do fast "get all alias for nick" queries...
	#	Consider going back to using integer IDs for this? I dunno if indexing integers is faster than TEXT in SQLite
	# if not exists:
	query.query('''SELECT name FROM sqlite_master WHERE name='alias_user_idx';''')
	if query.error:
		#uh oh....
		print "What happened?: %s" % query.error
		return False
	
	if not query.rows:
		query.query('''CREATE INDEX alias_user_idx ON alias(nick);''')
		if query.error:
			print "Error creating useralias index... %s" % query.error
			return False

	return True

#mappings to methods
mappings = (Mapping(types=["privmsg"], command="alias", function=alias),)
