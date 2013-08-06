from twisted.internet.threads import deferToThread

from settings import Settings
from sys import stderr
from traceback import format_exc
from os.path import join
from operator import attrgetter
from uuid import uuid1

from wrapper import BotWrapper
		
class Dispatcher:
	modules = []
	hostmap = {}
	hostwaitmap = {}
	#TYPES = ('action', 'connectionMade', 'irc_NICK', 'joined', 'privmsg', 
	#	'sendmsg', 'signedOn', 'userRenamed')

	# Construct the new hostmap, then overwrite the original when reload is complete.
	@classmethod
	def reload(cls, callback=None):
		print "LOADING..."
		moddir = join(Settings.cwd, "modules")
		
		#reload all modules I guess
		#here we should get modules from settings... Assume settings has been updated first.
		modulemap = {}
		hostmap = {}
		servers = Settings.servers
		for servername in servers:
			hostmap[servername] = {}
			hostmap[servername]["MSGHOOKS"] = False
			if servername not in cls.hostwaitmap:
				cls.hostwaitmap[servername] = {}
				# for type in cls.TYPES:
					# cls.hostwaitmap[servername][type] = {}
			# for type in cls.TYPES:
				# hostmap[servername][type] = {}
				# hostmap[servername][type]["instant"] = []
				# hostmap[servername][type]["command"] = {}
				# hostmap[servername][type]["regex"] = []
			if servers[servername].allowmodules:
				modulemap[servername] = servers[servername].allowmodules
			else: 
				modulemap[servername] = Settings.modules
			if servers[servername].denymodules:
				modulemap[servername].difference_update(servers[servername].denymodules)
		
		
		notloaded = []
		from imp import find_module, load_module
		moduledict = {}
		for modulename in Settings.modules:
			try:
				(f, pathname, description) = find_module(modulename, [moddir])
				try:
					module = load_module(modulename, f, pathname, description)
				except Exception as e:
					notloaded.append((modulename, format_exc()))
					continue
				finally:
					f.close()
			except Exception as e:
				notloaded.append((mod, format_exc()))
				continue
			# Catch errors that might be thrown on running module.init()
			try:
				if not module.init():
					notloaded.append((modulename, "Error in init()"))
					continue
			except Exception as e:
				notloaded.append((modulename, "Error in init():\n\n" + format_exc()))

			Settings.moduledict[modulename] = module
			for mapping in module.mappings:
				for type in mapping.types:
					# if type not in cls.TYPES:
						# print "WARNING UNSUPPORTED TYPE: %s" % type
						# continue

					type = type.lower()
					for servername in modulemap:
						if modulename not in modulemap[servername]:
							continue

						# There's no actual reason to restrict types to a preset list, and in some cases it might be annoying
						# (e.g. hooking a numeric event type)
						if type not in hostmap[servername]:
							hostmap[servername][type] = {}
							hostmap[servername][type]["instant"] = []
							hostmap[servername][type]["regex"] = []
							hostmap[servername][type]["command"] = {}
						if type not in cls.hostwaitmap[servername]:
							cls.hostwaitmap[servername][type] = {}
						# Add type to servernamemapping
						# This is _addmap inlined
						if type == "sendmsg":
							hostmap[servername]["MSGHOOKS"] = True
						if not mapping.command and not mapping.regex: 
							hostmap[servername][type]["instant"].append(mapping)
							hostmap[servername][type]["instant"].sort(key=attrgetter('priority'))

						if mapping.command:
							mapcom = mapping.command
							#check if tuple or list or basestring (str or unicodes)
							# I guess it's not a big deal to check both
							if isinstance(mapcom, list) or isinstance(mapcom, tuple):
								for commandname in mapcom:
									hostmap[servername][type]["command"].setdefault(commandname, []).append(mapping)
									hostmap[servername][type]["command"][commandname].sort(key=attrgetter('priority'))
							# TODO: unicode command?
							elif isinstance(mapcom, basestring):
								hostmap[servername][type]["command"].setdefault(mapcom, []).append(mapping)
								hostmap[servername][type]["command"][mapcom].sort(key=attrgetter('priority'))

						if mapping.regex:
							hostmap[servername][type]["regex"].append(mapping)
							hostmap[servername][type]["regex"].sort(key=attrgetter('priority'))

		if notloaded:
			print "WARNING: MODULE(S) NOT LOADED: %s" % ', '.join((x[0] for x in notloaded))
			for module, traceback in notloaded:
				print >> stderr, module + ':'
				print >> stderr, traceback
		else:
			cls.hostmap = hostmap
			print "All done."

	@classmethod
	def dispatch(cls, botinst, event):
		settings = botinst.settings
		servername = settings.name
		cont_or_wrap = settings.state.container
		if event.channel or event.nick:
			cont_or_wrap = BotWrapper(event, cont_or_wrap)
		msg = event.msg
		# Case insensitivity for types (convenience) (is this a bad idea?)
		type = event.type.lower()
		command = ""
		input = ""
		if type != "sendmsg" and msg and msg.startswith(settings.commandprefix):
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

		if type in cls.hostmap[servername]:
			#lol dispatcher is 100 more simple now, but at the cost of more dict...
			for mapping in cls.hostmap[servername][type]["instant"]:
				cls._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break #lol cheap and easy way to support total override
			#super fast command dispatching now... Only thing left that's slow is the regex but has to be
			for mapping in cls.hostmap[servername][type]["command"].get(command,()):
				cls._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break
			# TODO: Consider this:
			# super priority==0 override doesn't really make much sense on a regex, but whatever
			for mapping in cls.hostmap[servername][type]["regex"]:
				if mapping.regex.match(msg):
					cls._dispatchreally(mapping.function, event, cont_or_wrap)
					if mapping.priority == 0: break

		if type in cls.hostwaitmap[servername]:
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
		d.addErrback(cont_or_wrap._moduleerr)

	@classmethod
	def addWaitEvent(cls, servername, we):
		for i in we.interested:
			cls.hostwaitmap[servername][i][we.id] = we
		for s in we.stope:
			cls.hostwaitmap[servername][s][we.id] = we


