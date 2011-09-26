from twisted.internet.threads import deferToThread

from settings import Settings
from sys import stderr
from traceback import format_exc
from os.path import join

from state import State
from wrapper import BotWrapper
# class DispatchType:
	
	# def __init__(self):
		# self.instant = []
		# self.commands = []
		# self.regex = []

class Dispatcher:
	modules = []
	hostmap = {}
	TYPES = ("connectionMade", "signedOn", "joined", "privmsg", 
		"action", "irc_NICK", "sendmsg")
	
	@classmethod
	def _addmap(cls, sever, type, mapping):
		if type == "sendmsg":
			cls.hostmap[sever]["MSGHOOKS"] = True
		if (not mapping.command) and (not mapping.regex): 
			cls.hostmap[sever][type]["instant"].append(mapping.function)
		else:
			if mapping.command:
				cls.hostmap[sever][type]["command"].append((mapping.command, mapping.function))
			if mapping.regex:
				cls.hostmap[sever][type]["regex"].append((mapping.regex, mapping.function))
	
	@classmethod
	def reload(cls, callback=None):
		print "LOADING..."
		moddir = join(Settings.cwd, "modules")
		
		#reload all modules I guess
		#here we should get modules from settings... Assume settings has been updated first.
		modulemap = {}
		cls.hostmap = {}
		servers = Settings.servers
		for servername in servers:
			cls.hostmap[servername] = {}
			for type in cls.TYPES:
				cls.hostmap[servername][type] = {}
				cls.hostmap[servername]["MSGHOOKS"] = False
				cls.hostmap[servername][type]["instant"] = []
				cls.hostmap[servername][type]["command"] = []
				cls.hostmap[servername][type]["regex"] = []
			if servers[servername].allowmodules:
				modulemap[servername] = servers[servername].allowmodules
			else: 
				modulemap[servername] = Settings.modules
			if servers[servername].denymodules:
				modulemap[servername].difference_update(servers[servername].denymodules)
		
		
		notloaded = []
		from imp import find_module, load_module
		Settings.moduledict = {}
		for mod in Settings.modules:
			try:
				(f, pathname, description) = find_module(mod, [moddir])
				try:
					module = load_module(mod, f, pathname, description)
				except Exception as e:
					notloaded.append((mod, format_exc()))
					f.close()
					continue
			except Exception as e:
				notloaded.append((mod, format_exc))
				continue
			try:
				if module.init():
					Settings.moduledict[mod] = module
					#do stuff with module.mappings
					#cls.mappings[mod] = []
					for mapping in module.mappings:
						for type in mapping.types:
							if type not in cls.TYPES:
								print "WARNING UNSUPPORTED TYPE: %s" % type
							else:
								for server in modulemap:
									if mod in modulemap[server]:
										#add type to servermapping
										cls._addmap(server, type, mapping)		
				else:
					notloaded.append((mod, "Error in init()"))
			except Exception as e:
				notloaded.append((mod, format_exc))

		if notloaded:
			print "WARNING: MODULE(S) NOT LOADED: %s" % ', '.join((x[0] for x in notloaded))
			for module, traceback in notloaded:
				print >> stderr, module + ':'
				print >> stderr, traceback
		else: print "All done."
		
	
	@classmethod
	def dispatch(cls, servername, event):
		cont_or_wrap = State.networks[servername].container
		if event.channel:
			cont_or_wrap = BotWrapper(event, cont_or_wrap)
		msg = event.msg
		type = event.type
		command = ""
		input = ""
		if (type != "sendmsg") and msg and msg.startswith(Settings.servers[servername].commandprefix):
			#case insensitive match?
			#also this means that commands can't have spaces in them, and lol command prefix can't be a space
			#all are good to me, if you want a case sensitive match you can do your command as a regex - griff
			command = msg.split(" ", 1)
			if len(command) > 1:
				command, input = command
			else:
				command = command[0]
			# Only one character prefix? okay... (jk it's fine) - griff
			command = command[1:]
			# Maintain case for event, for funny things like replying in all caps
			event.command, event.input = (command, input)
			command = command.lower()
		
		#lol dispatcher is 100 more simple now, but at the cost of more dict...
		for func in cls.hostmap[servername][type]["instant"]:
			cls._dispatchreally(func, event, cont_or_wrap)
		for com, func in cls.hostmap[servername][type]["command"]:
			if command == com:
				cls._dispatchreally(func, event, cont_or_wrap)
		for regex, func in cls.hostmap[servername][type]["regex"]:
			if regex.match(msg):
				cls._dispatchreally(func, event, cont_or_wrap)

	@staticmethod					
	def _dispatchreally(func, event, cont_or_wrap):
		d = deferToThread(func, event, cont_or_wrap)
		#add callback and errback
		#I think we should just add an errback
		#d.addCallbacks(botinst.moduledata, botinst.moduleerr)
		d.addErrback(cont_or_wrap.moduleerr)
