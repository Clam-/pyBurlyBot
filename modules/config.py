#config module

from util import Mapping, argumentSplit
from util.settings import Settings

from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

from json import dumps, loads

PRIVATE_OPTIONS = set(("nickservpass",))

def servchanParse(servchan):
	# parse servchan
	if servchan == "-": 
		server = False
		channel = None
	elif servchan == "this":
		server = None
		channel = None #event.target will be set in wrapper
	else:
		if ":#" in servchan:
			server, channel = servchan.split(":", 1)
			if not server:
				server = False
		elif servchan.startswith("#"):
			server = None
			channel = servchan
		else:
			server = servchan
			channel = False
	return server, channel

def showhelp(bot):
	#show help? We should make some really nice framework for handling input
	# and help and stuff
	bot.say('%sconfig serverchannel module opt [value]. serverchannel = servername:#channel (channel on server) or '
	'servername (default for server) or :#channel (channel globally) or #channel (channel on this server) or "-" (default) '
	' or "this" (current channel (unless PM) current server.) module = "-" for non-module options. value should be JSON' % bot.getOption("commandprefix"))

def config(event, bot):
	#do some things
	command = ""
	if not bot.isadmin():
		bot.say("Good joke.")
		return
	
	if event.argument == "save":
		blockingCallFromThread(reactor, Settings.saveOptions)
		bot.say("Done (save is automatically done when setting config values.)")
		return
	elif event.argument:
		servchan, module, opt, value = argumentSplit(event.argument, 4)
	else: return showhelp(bot)
	
	# set or get value
	if servchan and module and opt:
		server, channel = servchanParse(servchan)
		
		if opt in PRIVATE_OPTIONS and not event.isPM():
			if value:
				bot.say("Use PM to set this option. If this is a password you probably want to change it now.")
				return
			else:
				bot.say("Use PM to get this option.")
				return
		if module == "-":
			module = None
		else:
			if not bot.isModuleAvailable(module):
				bot.say("module %s not available" % module)
			modopts = bot.getModule(module)
			if hasattr(modopts, "OPTIONS"):
				modopts = modopts.OPTIONS
			else:
				modopts = {}
		
		# set value
		if value:
			try:
				value = loads(value)
			except Exception as e:
				return bot.say("Error: %s" % e)
			tvalue = type(value)
			#get type for module type checking:
			if module and opt in modopts:
				t = modopts[opt][0]
				if not (t is tvalue):
					return bot.say("Incorrect type of %s: %s. Require %s." % (opt, tvalue, t))
			msg = "Set %%s(%%s) to %%s (was: %s)"
			try:
				old = bot.getOption(opt, server=server, channel=channel, module=module)
				msg = msg % dumps(old)
			except AttributeError:
				msg = msg % "unset"
			except Exception as e:
				return bot.say("Error: %s" % e)
			# check type of non module option:
			if not module:
				t = type(old)
				if not t is tvalue:
					return bot.sat("Incorrect type of %s: %s. Require %s." % (opt, tvalue, t))
			try:
				bot.setOption(opt, value, server=server, channel=channel, module=module)
			except Exception as e:
				return bot.say("Error: %s" % e)
			bot.say(msg % (opt, servchan, dumps(value)))
		
		#get value
		else:
			try:
				value = dumps(bot.getOption(opt, server=server, channel=channel, module=module))
			except Exception as e:
				return bot.say("Error: %s" % e)
			if module and opt in modopts:
				t, desc, default = modopts[opt]
				bot.say("Setting for %s(%s) is %s. %s Type: %s, Default: %s" % (opt, servchan, value, desc, t.__name__, dumps(default)))
			else:
				bot.say("Setting for %s(%s) is %s" % (opt, servchan, value))
	else:
		return showhelp(bot)
	
#mappings to methods
mappings = (Mapping(command="config", function=config),)
