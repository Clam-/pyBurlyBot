
class BotWrapper:

	def __init__(self, event, botcont):
		self.source = event.channel
		self.event = event
		self._botcont = botcont
		
	def __getattr__(self, name):
		if name in self.__dict__: return getattr(self, name)
		return getattr(self._botcont, name)
		
	def say(self, msg):
		self.msg(self.source, msg)
		
	def isadmin(self, module=None):
		if not self.event.nick: return None
		if module:
			return self.event.nick in self._botcont.settings.getModuleOption(module, "admins")
		else:
			return self.event.nick in self._botcont.settings.admin
		
		

# some reasoning for this:	
# >>> import wrapper
# >>> class Container:
# ...  def __init__(self, lol):
# ...   self.lol = lol
# ...  def msg(self, dest, msg):
# ...   print "DEST:",dest,"MSG:",msg
# ...
# >>>
# >>> c = Container("something")
# >>> class Event:
# ...  def __init__(self, source):
# ...   self.channel = source
# ...
# >>>
# >>> e = Event("THIS SOURCE")
# >>> bt = wrapper.BotWrapper(e, c)
# >>> bt
# <wrapper.BotWrapper instance at 0x01FF1918>
# >>> bt.say("aeuhaeuhaeuh")
# DEST: THIS SOURCE MSG: aeuhaeuhaeuh
# >>> bt.msg("lol")
# Traceback (most recent call last):
  # File "<stdin>", line 1, in <module>
# TypeError: msg() takes exactly 3 arguments (2 given)
# >>> bt.msg("DIFFERENT SOURCE", "lol")
# DEST: DIFFERENT SOURCE MSG: lol
# >>>
