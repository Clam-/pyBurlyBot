from twisted.internet.threads import deferToThread

from sys import stderr
from traceback import format_exc
from os.path import join
from operator import attrgetter
from uuid import uuid1
from imp import find_module, load_module

from wrapper import BotWrapper
from container import SetupContainer
class Dispatcher:
	MODULEDICT = {}
	NOTLOADED = []
	
	def __init__(self, settings):
		moddir = join(settings.botdir, "modules")
		
		self.eventmap = {}
		self.waitmap = {} #TODO: finish this
		self.MSGHOOKS = False
		self.settings = settings
		
		# prepare list of modules to be loaded
		self.allowedmodules = settings.allowmodules if settings.allowmodules else settings.modules
		# remove denied modules
		if settings.denymodules:
			self.allowedmodules = allowedmodules.difference(settings.denymodules)

		# load modules if they haven't been loaded before
		for modulename in self.allowedmodules:
			if modulename not in self.MODULEDICT:
				self.loadModule(moddir, modulename)

	def checkAndLoadReqs(self, moddir, module, resolvedmodules):
		reqs = module.REQUIRES
		if not isinstance(reqs, tuple) or isinstance(reqs, list):
			reqs = (reqs,) #assume string?
		for req in reqs:
			if req in self.MODULEDICT: continue
			else:
				#attempt to load
				if req not in self.allowedmodules:
					return False
				if not self.loadModule(moddir, req, resolvedmodules):
					return None
		return True
				
	def loadModule(self, moddir, modulename, resolvedmodules=[]):
		print "Loading %s..." % modulename
		if modulename in resolvedmodules:
			self.NOTLOADED.append((modulename, "Circular module dependency. Parents: %s" % (modulename, resolvedmodules)))
			return None
		module = None
		try:
			(f, pathname, description) = find_module(modulename, [moddir])
			try:
				module = load_module(modulename, f, pathname, description)
			except Exception as e:
				self.NOTLOADED.append((modulename, format_exc()))
				return None
			finally:
				f.close()
		except Exception as e:
			self.NOTLOADED.append((modulename, format_exc()))
			return None
		# if haven't loaded before, run init()
		# Catch errors that might be thrown on running module.init()
		if not hasattr(module, "mappings"):
			self.NOTLOADED.append((modulename, "Missing 'mappings'"))
			return None
		# process module requirements before calling init:
		if hasattr(module, "REQUIRES"):
			reqsloaded = self.checkAndLoadReqs(moddir, module, resolvedmodules if resolvedmodules else [modulename])
			if reqsloaded is False:
				self.NOTLOADED.append((modulename, "Requirement cannot be loaded because it's not allowed. (add to allowmodules)"))
				return None
			elif reqsloaded is None:
				self.NOTLOADED.append((modulename, "Requirements cannot be loaded."))
				return None
		print "processing init of %s" % modulename
		#process module init if it has one
		if hasattr(module, "init"):
			try:
				if not module.init(SetupContainer(self.settings.container)):
					self.NOTLOADED.append((modulename, "Error in init()"))
					return None
			except Exception as e:
				self.NOTLOADED.append((modulename, "Error in init():\n\n" + format_exc()))
				return None
		self.MODULEDICT[modulename] = module
		self.processMappings(module)
		print "Loaded %s." % modulename
		print Dispatcher.MODULEDICT
		return True
		
	def processMappings(self, module):
		eventmap = self.eventmap
		for mapping in module.mappings:
			for type in mapping.types:

				type = type.lower()
				
				# There's no actual reason to restrict types to a preset list, and in some cases it might be annoying
				# (e.g. hooking a numeric event type)
				if type not in eventmap:
					eventmap[type] = {}
					eventmap[type]["instant"] = []
					eventmap[type]["regex"] = []
					eventmap[type]["command"] = {}
				#TODO: waitevent map?
				
				# Add type to servernamemapping
				# This is _addmap inlined
				if type == "sendmsg":
					self.MSGHOOKS = True
				if not mapping.command and not mapping.regex: 
					eventmap[type]["instant"].append(mapping)
					eventmap[type]["instant"].sort(key=attrgetter('priority'))

				if mapping.command:
					mapcom = mapping.command
					#check if tuple or list or basestring (str or unicodes)
					# I guess it's not a big deal to check both
					if isinstance(mapcom, list) or isinstance(mapcom, tuple):
						for commandname in mapcom:
							eventmap[type]["command"].setdefault(commandname, []).append(mapping)
							eventmap[type]["command"][commandname].sort(key=attrgetter('priority'))
					# TODO: unicode command?
					elif isinstance(mapcom, basestring):
						eventmap[type]["command"].setdefault(mapcom, []).append(mapping)
						eventmap[type]["command"][mapcom].sort(key=attrgetter('priority'))

				if mapping.regex:
					eventmap[type]["regex"].append(mapping)
					eventmap[type]["regex"].sort(key=attrgetter('priority'))
	
	@classmethod
	def reset(cls):
		MODULEDICT = {}
		NOTLOADED = []
	
	def dispatch(self, botinst, event):
		settings = self.settings
		servername = settings.serverlabel
		cont_or_wrap = botinst.container
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
		
		eventmap = self.eventmap
		if type in eventmap:
			#lol dispatcher is 100 more simple now, but at the cost of more dict...
			for mapping in eventmap[type]["instant"]:
				self._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break #lol cheap and easy way to support total override
			#super fast command dispatching now... Only thing left that's slow is the regex but has to be
			for mapping in eventmap[type]["command"].get(command,()):
				self._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break
			# TODO: Consider this:
			# super priority==0 override doesn't really make much sense on a regex, but whatever
			for mapping in eventmap[type]["regex"]:
				if mapping.regex.match(msg):
					self._dispatchreally(mapping.function, event, cont_or_wrap)
					if mapping.priority == 0: break

		if type in self.waitmap:
			#special map to deal with WaitEvents
			for wekey in self.waitmap[servername][type]:
				we = self.waitmap[servername][type][wekey]
				if type in we.stope:
					we.q.done = True
					for i in we.intereste:
						try: del self.waitmap[servername][i][wekey]
						except Exception as e: print "Already removed(?): %s" % e
					for s in we.stopevents:
						try: del self.waitmap[servername][s][wekey]
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


	@classmethod
	def showLoadErrors(cls):
		if cls.NOTLOADED:
			print "WARNING: MODULE(S) NOT LOADED: %s" % ', '.join((x[0] for x in cls.NOTLOADED))
			for module, traceback in cls.NOTLOADED:
				print >> stderr, module + ':'
				print >> stderr, traceback

