from twisted.internet.threads import deferToThread

from sys import stderr
from traceback import format_exc, print_exc
from os.path import join
from operator import attrgetter
from uuid import uuid1
from imp import find_module, load_module
from functools import partial

from wrapper import BotWrapper
from container import SetupContainer
from helpers import isIterable, commandSplit, coerceToUnicode
from event import Event

class Dispatcher:
	MODULEDICT = {}
	NOTLOADED = {}
	
	def __init__(self, settings):
		self.moddir = join(settings.botdir, "modules")
		self.waitmap = {}
		self.settings = settings
		self.debug = settings.debug
		self.reload()

	def reload(self):
		#temporary set to keep track of what we have loaded
		self.loadedModules = set()
		
		self.eventmap = {}
		# don't clear waitmap on reload to allow for still waiting functions to pass
		# it's also self managed (hopefully)
		
		self.MSGHOOKS = False
		
		settings = self.settings
		# prepare list of modules to be loaded
		self.allowedmodules = settings.allowmodules if settings.allowmodules else settings.modules
		# remove denied modules
		if settings.denymodules:
			self.allowedmodules = self.allowedmodules - settings.denymodules

		# load modules
		for modulename in self.allowedmodules:
			self.loadModule(modulename)
	
	def checkAndLoadReqs(self, module, resolvedModules):
		reqs = module.REQUIRES
		if not isIterable(reqs):
			reqs = (reqs,) #assume string?
		for req in reqs:
			if req in self.loadedModules: continue
			else:
				#attempt to load
				if req not in self.allowedmodules:
					return False
				if not self.loadModule(req, resolvedModules):
					return None
		return True
	
	def loadModule(self, modulename, resolvedModules=None):
		if modulename in self.loadedModules: return True
		print "Loading %s..." % modulename
		if resolvedModules and modulename in resolvedModules:
			self.NOTLOADED[modulename] = "Circular module dependency. Parents: %s" % (resolvedModules)
			return None
		module = self.MODULEDICT.get(modulename, None)
		if module is None:
			if modulename in self.NOTLOADED: return None
			try:
				(f, pathname, description) = find_module(modulename, [self.moddir])
				try:
					# prefix module name to make sure no sys.modules clashes
					module = load_module("pyBurlyBot_%s" % modulename, f, pathname, description)
				except Exception as e:
					self.NOTLOADED[modulename] = format_exc()
					return None
				finally:
					f.close()
			except Exception as e:
				self.NOTLOADED[modulename] = format_exc()
				return None
		# process module requirements before calling init:
		if hasattr(module, "REQUIRES"):
			if not resolvedModules: resolvedModules = set([modulename])
			else: resolvedModules.add(modulename)
			reqsloaded = self.checkAndLoadReqs(module, resolvedModules)
			# TODO: consider telling the user what requirement was failed.
			if reqsloaded is False:
				self.NOTLOADED[modulename] = "Requirement cannot be loaded because they are not allowed. (add to modules/allowmodules)"
				return None
			elif reqsloaded is None:
				self.NOTLOADED[modulename] = "Requirements cannot be loaded."
				return None
		
		# process module default settings
		if hasattr(module, "OPTIONS"):
			for opt, params in module.OPTIONS.iteritems():
				if len(params) != 3:
					self.NOTLOADED[modulename] = "Invalid number of parameters for OPTIONS. Require: type, desc, default."
					return None
				#using getOption because it already has all the functionality coded in to do this default option setting.
				self.settings.getOption(opt, server=False, module=modulename, default=params[2], setDefault=True)
		# load init() per dispatcher/server
		# Catch errors that might be thrown on running module.init()
		if hasattr(module, "init"):
			try:
				if not module.init(SetupContainer(self.settings.container)):
					self.NOTLOADED[modulename] = "Error in init() for server (%s)" % self.settings.serverlabel
					return None
			except Exception as e:
				self.NOTLOADED[modulename] = "Error in init() for server (%s):\n%s" % (self.settings.serverlabel, format_exc())
				return None
		
		# check provides (AFTER init) and add them to ADDONS
		if hasattr(module, "PROVIDES"):
			for item in module.PROVIDES:
				try:
					self.settings.addons._add(item, modulename, getattr(module, item))
				except AttributeError:
					self.NOTLOADED[modulename] = "Error in PROVIDES for server (%s):\n%s" % (self.settings.serverlabel, format_exc())
					return None
		
		self.MODULEDICT[modulename] = module
		if hasattr(module, "mappings"):
			self.processMappings(module)
		print "Loaded %s." % modulename
		self.loadedModules.add(modulename)
		return True
		
	def processMappings(self, module):
		eventmap = self.eventmap
		for mapping in module.mappings:
			for etype in mapping.types:
				etype = etype.lower()

				if etype not in eventmap:
					eventmap[etype] = {}
					eventmap[etype]["instant"] = []
					eventmap[etype]["regex"] = []
					eventmap[etype]["command"] = {}

				if etype == "sendmsg" and mapping.override:
					self.MSGHOOKS = True
				if not mapping.command and not mapping.regex: 
					eventmap[etype]["instant"].append(mapping)
					eventmap[etype]["instant"].sort(key=attrgetter('priority'))

				if mapping.command:
					mapcom = mapping.command
					#check if tuple or list or basestring (str or unicodes)
					# I guess it's not a big deal to check both
					if mapping.function and isinstance(mapping.function, partial):
						# little cheat for adding module to functools.partial things like in simplecommands
						mapping.function.__module__ = module.__name__
					for commandname in mapcom:
						eventmap[etype]["command"].setdefault(commandname, []).append(mapping)
						eventmap[etype]["command"][commandname].sort(key=attrgetter('priority'))

				if mapping.regex:
					eventmap[etype]["regex"].append(mapping)
					eventmap[etype]["regex"].sort(key=attrgetter('priority'))
	
	def getCommandFuncs(self, cmd):
		cmds = []
		for mapping in self.eventmap.get("privmsged", {}).get("command", {}).get(cmd, []):
			cmds.append((mapping.function, mapping.command))
		return cmds
	
	def getCommands(self):
		commands = set([])
		for mappings in self.eventmap.get("privmsged", {}).get("command", {}).values():
			for mapping in mappings: commands.add(mapping.command[0])
		return list(commands)
	
	@classmethod
	def reset(cls):
		cls.unloadModules()
		cls.MODULEDICT.clear()
		cls.NOTLOADED.clear()

	@classmethod
	def unloadModules(cls):
		# call modules unload function to clean up.
		for modname, module in cls.MODULEDICT.iteritems():
			if hasattr(module, "unload"): 
				print "UNLOADING (%s)" % modname
				try: module.unload()
				except Exception as e:
					print "ERROR in unloading %s" % modname
					print_exc()
	
	def dispatch(self, botinst, event_type, **eventkwargs):
		settings = self.settings
		cont_or_wrap = botinst.container
		event = None
		# Case insensitivity for event_type lookups
		l_event_type = event_type.lower()
		dispatched = False
		
		msg = eventkwargs.get("msg", None)
		if msg and l_event_type != "sendmsg": eventkwargs["msg"] = msg = coerceToUnicode(eventkwargs["msg"], settings.encoding)
		command = ""
		if l_event_type != "sendmsg" and msg and msg.startswith(settings.commandprefix):
			#case insensitive command (see below)
			#commands can't have spaces in them, and lol command prefix can't be a space
			#if you want a case sensitive match you can do your command as a regex
			command, argument = commandSplit(msg)
			#support multiple character commandprefix
			command = command[len(settings.commandprefix):]
			# Maintain case for event, for funny things like replying in all caps
			eventkwargs["command"], eventkwargs["argument"] = (command, argument)
			command = command.lower()
		eventmap = self.eventmap
		if l_event_type in eventmap:
			# TODO: Event and wrapper creation could possible be delayed even further maybe
			if event is None: 
				eventkwargs["encoding"] = settings.encoding
				event, cont_or_wrap = self.createEventAndWrap(cont_or_wrap, l_event_type, eventkwargs)
			if self.debug >= 2: print "DISPATCHING: %s" % event
			#lol dispatcher is 100 more simple now, but at the cost of more dict...
			for mapping in eventmap[l_event_type]["instant"]:
				self._dispatchreally(mapping.function, event, cont_or_wrap, self.debug)
				dispatched = True
				if mapping.priority == 0: break #lol cheap and easy way to support total override
			#super fast command dispatching now... Only thing left that's slow is the regex but has to be
			for mapping in eventmap[l_event_type]["command"].get(command,()):
				if mapping.admin and (event.nick.lower() not in settings.admins):
					# TODO: Do we bot.say("access denied") ?
					continue
				self._dispatchreally(mapping.function, event, cont_or_wrap, self.debug)
				dispatched = True
				if mapping.priority == 0: break
			# TODO: Consider this:
			# super priority==0 override doesn't really make much sense on a regex, but whatever
			for mapping in eventmap[l_event_type]["regex"]:
				result = mapping.regex.search(msg)
				if result:
					event.regex_match = result
					self._dispatchreally(mapping.function, event, cont_or_wrap, self.debug)
					dispatched = True
					if mapping.priority == 0: break

		if l_event_type in self.waitmap:
			#special map to deal with WaitData
			#delayed event creation as late as possible:
			if event is None: 
				event, cont_or_wrap = self.createEventAndWrap(cont_or_wrap, event_type, eventkwargs)
			wdset = self.waitmap[l_event_type]
			remove = []
			for wd in wdset:
				# if found stopevent add it to list to remove after iteration
				if l_event_type in wd.stope:
					remove.append(wd)
					wd.q.put(event)
					wd.done = True
					dispatched = True
				elif l_event_type in wd.interestede:
					wd.q.put(event)
					dispatched = True
			if remove:
				for x in remove:
					self.delWaitData(x)
		return dispatched
		
	@staticmethod
	def createEventAndWrap(cont_or_wrap, eventtype, eventkwargs):
		event = Event(eventtype, **eventkwargs)
		if event.target or event.nick:
			return event, BotWrapper(event, cont_or_wrap)
		else:
			return event, cont_or_wrap
	
	@staticmethod					
	def _dispatchreally(func, event, cont_or_wrap, debug):
		if debug >= 2: print "DISPATCHING TO: %r" % func
		d = deferToThread(func, event, cont_or_wrap)
		#add errback
		d.addErrback(cont_or_wrap._moduleerr)

	def addWaitData(self, wd):
		for ietype in wd.interestede:
			self.waitmap.setdefault(ietype, set()).add(wd)
		for setype in wd.stope:
			self.waitmap.setdefault(setype, set()).add(wd)
		print self.waitmap

	def delWaitData(self, wd):
		for wdtype in (wd.interestede, wd.stope):
			for etype in wdtype:
				wdset = self.waitmap.get(etype)
				if wdset:
					try: wdset.remove(wd)
					except KeyError: pass
				if not wdset:
					self.waitmap.pop(etype, None)
		
	@classmethod
	def showLoadErrors(cls):
		if cls.NOTLOADED:
			print "WARNING: MODULE(S) NOT LOADED: %s" % ', '.join(cls.NOTLOADED.iterkeys())
			for module, reason in cls.NOTLOADED.iteritems():
				print >> stderr, module + ':'
				print >> stderr, reason
