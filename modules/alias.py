#alias module
from re import compile as recompile
from util import Mapping
from Queue import Queue
from settings import Settings

def getNick(alias, db, results):
	db.put(('''SELECT nick FROM alias WHERE alias = ?;''', results, (alias,)))
	result = results.get()
	if result[0] == "SUCCESS":
		#check rows...
		if not result[1]:
			#if no results:
			return None
		else:
			return result[1][0]["nick"]
	else:
		print "Something very wrong happened: %s" % result[1]

def addalias(nick, alias, db, results):
	db.put(('''INSERT INTO alias (alias, nick) VALUES (?,?)''', results, (alias, nick)))
	result = results.get()
	if result[0] != "SUCCESS":
		print "Something wrong with aliasadd %s" % result[1]
		return False
	return True

def _listalias(nick, db, results):
	aliases = []
	db.put(('''SELECT alias FROM alias WHERE nick = ?''', results, (nick,)))
	result = results.get()
	if result[0] != "SUCCESS":
		print "Something wrong with aliaslist %s" % result[1]
	else:
		for row in result[1]:
			aliases.append(row['alias'])
	return aliases
		
def alias(event, botinst, db):
	# parse input "add" "del", etc
	#lol Griff can fix all this up. Debug onry
	results = Queue()
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
		nnick = getNick(new, db, results)
		if nnick:
			#alias already in use by nnick
			botinst.msg(event.channel, "Nick already in use by %s" % nnick)
			return
		nick = getNick(source, db, results)
		if not nick:
			#look for user
			db.put(('''SELECT 1 FROM user WHERE nick = ?''', results, (source,)))
			result = results.get()
			if result[0] == "SUCCESS":
				if result[1]:
					#exists
					if addalias(source, new, db, results):
						botinst.msg(event.channel, "Added %s to %s" % (new, source))
				else:
					botinst.msg(event.channel, "%s not seen before." % source)
					return
				
			else:
				print "Something really bad aaa %s" % result[1]
				return
			
		else:
			#add new to nick-source
			if addalias(nick, new, db, results):
				botinst.msg(event.channel, "Added %s to %s" % (new, nick))
	elif command == "del":
		if not input:
			botinst.msg(event.channel, "Need alias to remove")
			return
		#just blindly delete?
		#well I guess check if exists at least
		db.put(('''SELECT 1 FROM alias WHERE alias = ?''', results, (input,)))
		result = results.get()
		if result[0] == "SUCCESS":
			if result[1]:
				#exists
				#okay to try delete
				db.put(('''DELETE FROM alias WHERE alias = ?''', results, (input,)))
				if result[0] != "SUCCESS":
					botinst.msg(event.channel, "Remove of alias failed: %s" % result[1])
			else:
				botinst.msg(event.channel, "%s alias not found" % input)
		else:
			print "bad happen bbb %s" % result[1]	
	
	else:
		#show aliases:
		source = event.input
		if not source: source = event.nick
		#look for specific user
		nick = getNick(source, db, results)
		if nick:
			aliases = _listalias(nick, db, results)
			botinst.msg(event.channel, "Aliases for %s: %s" % (nick, ", ".join(aliases)))
			return
		else:
			#check for actual nick, actually, just blind it...
			# can do fancy later
			aliases = _listalias(source, db, results)
			botinst.msg(event.channel, "Aliases for %s: %s" % (source, ", ".join(aliases)))
	return

#init should always be here to setup needed DB tables or objects or whatever
def init(db):
	"""Do startup module things. This sample just checks if table exists. If not, creates it."""
	#require that user is loaded already:
	if "users" not in Settings.moduledict:
		print "ERROR LOADING ALIAS: REQUIREMENT OF users MODULE NOT MET"
		return False
	
	results = Queue()
	db.put(("SELECT name FROM sqlite_master WHERE name='alias'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''
create table alias(
	alias TEXT PRIMARY KEY,
	nick TEXT
);''', results))
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating table... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
	
	#index alias column
	#Unique does this for us
	#but should index nick column so can do fast "get all alias for nick" queries...
	#	Consider going back to using integer IDs for this? I dunno if indexing integers is faster than TEXT in SQLite
	# if not exists:
	db.put(("SELECT name FROM sqlite_master WHERE name='alias_user_idx'", results))
	result = results.get()
	if result[0] == "SUCCESS":
		#good
		if not result[1]:
			db.put(('''CREATE INDEX alias_user_idx ON alias(nick);''', results))
			result = results.get()
			if result[0] != "SUCCESS":
				print "Error creating useralias index... %s" % result[1]
				return False
	else:
		#uh oh....
		print "What happened?: %s" % result[1]
		return False
	return True

#mappings to methods
mappings = (Mapping(type=["privmsg"], command="alias", function=alias),)