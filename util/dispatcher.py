from twisted.internet.threads import deferToThread

from sys import stderr
from traceback import format_exc
from os.path import join
from operator import attrgetter
from uuid import uuid1
from imp import find_module, load_module

from wrapper import BotWrapper
from container import SetupContainer
from helpers import isIterable, commandSplit, coerceToUnicode
from event import Event

class Dispatcher:
	MODULEDICT = {}
	NOTLOADED = []
	
	def __init__(self, settings):
		self.moddir = join(settings.botdir, "modules")
		self.waitmap = {}
		self.settings = settings
		self.reload()

	def reload(self):
		self.eventmap = {}
		# don't clear waitmap on reload to allow for still waiting functions to pass
		# it's also self managed (hopefully)
		
		self.MSGHOOKS = False
		
		settings = self.settings
		# prepare list of modules to be loaded
		self.allowedmodules = settings.allowmodules if settings.allowmodules else settings.modules
		# remove denied modules
		if settings.denymodules:
			self.allowedmodules = allowedmodules.difference(settings.denymodules)

		# load modules if they haven't been loaded before
		for modulename in self.allowedmodules:
			if modulename not in self.MODULEDICT:
				self.loadModule(modulename)
	
	def checkAndLoadReqs(self, module, resolvedmodules):
		reqs = module.REQUIRES
		if not isIterable(reqs):
			reqs = (reqs,) #assume string?
		for req in reqs:
			if req in self.MODULEDICT: continue
			else:
				#attempt to load
				if req not in self.allowedmodules:
					return False
				if not self.loadModule(req, resolvedmodules):
					return None
		return True
				
	def loadModule(self, modulename, resolvedmodules=[]):
		print "Loading %s..." % modulename
		if modulename in resolvedmodules:
			self.NOTLOADED.append((modulename, "Circular module dependency. Parents: %s" % (modulename, resolvedmodules)))
			return None
		module = None
		try:
			(f, pathname, description) = find_module(modulename, [self.moddir])
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
			reqsloaded = self.checkAndLoadReqs(module, resolvedmodules if resolvedmodules else [modulename])
			if reqsloaded is False:
				self.NOTLOADED.append((modulename, "Requirement cannot be loaded because it's not allowed. (add to allowmodules)"))
				return None
			elif reqsloaded is None:
				self.NOTLOADED.append((modulename, "Requirements cannot be loaded."))
				return None
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
		return True
		
	def processMappings(self, module):
		eventmap = self.eventmap
		for mapping in module.mappings:
			for etype in mapping.types:

				etype = etype.lower()
				
				# There's no actual reason to restrict etypes to a preset list, and in some cases it might be annoying
				# (e.g. hooking a numeric event etype)
				if etype not in eventmap:
					eventmap[etype] = {}
					eventmap[etype]["instant"] = []
					eventmap[etype]["regex"] = []
					eventmap[etype]["command"] = {}
				
				# Add etype to servernamemapping
				# This is _addmap inlined
				if etype == "sendmsg":
					self.MSGHOOKS = True
				if not mapping.command and not mapping.regex: 
					eventmap[etype]["instant"].append(mapping)
					eventmap[etype]["instant"].sort(key=attrgetter('priority'))

				if mapping.command:
					mapcom = mapping.command
					#check if tuple or list or basestring (str or unicodes)
					# I guess it's not a big deal to check both
					if isIterable(mapcom):
						for commandname in mapcom:
							eventmap[etype]["command"].setdefault(commandname, []).append(mapping)
							eventmap[etype]["command"][commandname].sort(key=attrgetter('priority'))
					# TODO: unicode command, should work...
					elif isinstance(mapcom, basestring):
						eventmap[etype]["command"].setdefault(mapcom, []).append(mapping)
						eventmap[etype]["command"][mapcom].sort(key=attrgetter('priority'))

				if mapping.regex:
					eventmap[etype]["regex"].append(mapping)
					eventmap[etype]["regex"].sort(key=attrgetter('priority'))
	
	@classmethod
	def reset(cls):
		cls.MODULEDICT = {}
		cls.NOTLOADED = []
	
	def dispatch(self, botinst, eventtype, **eventkwargs):
		settings = self.settings
		servername = settings.serverlabel
		cont_or_wrap = botinst.container
		event = None
		# Case insensitivity for etypes (convenience) 
		#TODO: (is this a bad idea?)
		eventtype = eventtype.lower()
		
		msg = eventkwargs.get("msg", None)
		if msg and eventtype != "sendmsg": eventkwargs["msg"] = msg = coerceToUnicode(eventkwargs["msg"], settings.encoding)
		command = ""
		if eventtype != "sendmsg" and msg and msg.startswith(settings.commandprefix):
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
		if eventtype in eventmap:
			#delayed event creation as late as possible:
			if event is None: 
				eventkwargs["encoding"] = settings.encoding
				event, cont_or_wrap = self.createEventAndWrap(cont_or_wrap, eventtype, eventkwargs)
			#lol dispatcher is 100 more simple now, but at the cost of more dict...
			for mapping in eventmap[eventtype]["instant"]:
				self._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break #lol cheap and easy way to support total override
			#super fast command dispatching now... Only thing left that's slow is the regex but has to be
			for mapping in eventmap[eventtype]["command"].get(command,()):
				self._dispatchreally(mapping.function, event, cont_or_wrap)
				if mapping.priority == 0: break
			# TODO: Consider this:
			# super priority==0 override doesn't really make much sense on a regex, but whatever
			for mapping in eventmap[eventtype]["regex"]:
				if mapping.regex.match(msg):
					self._dispatchreally(mapping.function, event, cont_or_wrap)
					if mapping.priority == 0: break
		
		if eventtype in self.waitmap:
			#special map to deal with WaitData
			#delayed event creation as late as possible:
			if event is None: 
				event, cont_or_wrap = self.createEventAndWrap(cont_or_wrap, eventtype, eventkwargs)
			wdset = self.waitmap[eventtype]
			remove = []
			for wd in wdset:
				# if found stopevent add it to list to remove after iteration
				if eventtype in wd.stope:
					remove.append(wd)
					wd.q.put(event)
					wd.done = True
				elif eventtype in wd.interestede:
					wd.q.put(event)
			if remove:
				for x in remove:
					self.delWaitData(x)
	
	def createEventAndWrap(self, cont_or_wrap, eventtype, eventkwargs):
		event = Event(eventtype, **eventkwargs)
		if event.target or event.nick:
			return event, BotWrapper(event, cont_or_wrap)
		else:
			return event
	
	@staticmethod					
	def _dispatchreally(func, event, cont_or_wrap):
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
			print "WARNING: MODULE(S) NOT LOADED: %s" % ', '.join((x[0] for x in cls.NOTLOADED))
			for module, traceback in cls.NOTLOADED:
				print >> stderr, module + ':'
				print >> stderr, traceback
