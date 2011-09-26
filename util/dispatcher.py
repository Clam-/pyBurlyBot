from twisted.internet.threads import deferToThread

from settings import Settings
from sys import stderr
from traceback import format_exc
from os.path import join
from operator import attrgetter
from uuid import uuid1

from state import State
from wrapper import BotWrapper
		
class Dispatcher:
	modules = []
	hostmap = {}
	hostwaitmap = {}
	TYPES = ("connectionMade", "signedOn", "joined", "privmsg", 
		"action", "irc_NICK", "sendmsg")
	
	@classmethod
	def _addmap(cls, sever, type, mapping):
		if type == "sendmsg":
			cls.hostmap[sever]["MSGHOOKS"] = True
		if (not mapping.command) and (not mapping.regex): 
			cls.hostmap[sever][type]["instant"].append(mapping)
			cls.hostmap[sever][type]["instant"].sort(key=attrgetter('priority'))
		else:
			if mapping.command:
				#check if tuple or list or basestring (str or unicodes)
				# I guess it's not a big deal to check both
				mapcom = mapping.command
				if isinstance(mapcom, list) or isinstance(mapcom, tuple):
					for com in mapcom:
						if com in cls.hostmap[sever][type]["command"]:
							cls.hostmap[sever][type]["command"][com].append(mapping)
						else:
							cls.hostmap[sever][type]["command"][com] = [mapping]
						cls.hostmap[sever][type]["command"][com].sort(key=attrgetter('priority'))	
				elif isinstance(mapcom, basestring):
					if mapcom in cls.hostmap[sever][type]["command"]:
						cls.hostmap[sever][type]["command"][mapcom].append(mapping)
					else:
						cls.hostmap[sever][type]["command"][mapcom] = [mapping]
				cls.hostmap[sever][type]["command"][mapcom].sort(key=attrgetter('priority'))
			
			if mapping.regex:
				cls.hostmap[sever][type]["regex"].append(mapping)
				cls.hostmap[sever][type]["regex"].sort(key=attrgetter('priority'))
	
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
			if servername not in cls.hostwaitmap:
				cls.hostwaitmap[servername] = {}
				for type in cls.TYPES:
					cls.hostwaitmap[servername][type] = {}
			for type in cls.TYPES:
				cls.hostmap[servername][type] = {}
				cls.hostmap[servername]["MSGHOOKS"] = False
				cls.hostmap[servername][type]["instant"] = []
				cls.hostmap[servername][type]["command"] = {}
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
		
	#TODO: Put a Queue somewhere so that events that happen while a RELOAD is in progress can be queued and then processed
	#		after the reload
	#	Either that, or maybe we should construct the new hostmap, then overwrite the original when reload is complete.
	#		10million easier to do the latter, but the current reload implementation would need to be changed a little to
	#		pass around the temporary hostmap
	#	
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
		for mapping in cls.hostmap[servername][type]["instant"]:
			cls._dispatchreally(mapping.function, event, cont_or_wrap)
			if mapping.priority == 0: break #lol cheap and easy way to support total override
		#super fast command dispatching now... Only thing left that's slow is the regex but has to be
		if command in cls.hostmap[servername][type]["command"]:
			for mapping in cls.hostmap[servername][type]["command"][command]:
				cls._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break
		# TODO: Considder this:
		# super priority==0 override doesn't really make much sense on a regex, but whatever
		for mapping in cls.hostmap[servername][type]["regex"]:
			if mapping.regex.match(msg):
				cls._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break
				
		#special map to deal with WaitEvents
		for wekey in cls.hostwaitmap[servername][type]:
			we = cls.hostwaitmap[servername][type][wekey]
			if type in we.stope:
				we.q.done = True
				for i in we.intereste:
					try: del cls.hostwaitmap[servername][i][wekey]
					except Exception as e: print "Already removed(?): %s" % e
				for s in we.stopevents:
					try: del cls.hostwaitmap[servername][s][wekey]
					except Exception as e: print "Already removed(?): %s" % e
			elif type in we.interestede:
				we.q.put(event)
			
	@staticmethod					
	def _dispatchreally(func, event, cont_or_wrap):
		d = deferToThread(func, event, cont_or_wrap)
		#add callback and errback
		#I think we should just add an errback
		#d.addCallbacks(botinst.moduledata, botinst.moduleerr)
		d.addErrback(cont_or_wrap.moduleerr)

	@classmethod
	def addWaitEvent(cls, we):
		for i in we.interested:
			cls.hostwaitmap[servername][i][we.id] = we
		for s in we.stope:
			cls.hostwaitmap[servername][s][we.id] = we

		