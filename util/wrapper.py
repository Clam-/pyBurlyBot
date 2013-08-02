# This seems like a bit of a waste, but it's difficult to implement this in Container
#  because of the reliance on event data.
# I don't really like creating one of these every dispatch.
class BotWrapper:

	def __init__(self, event, botcont):
		self.event = event
		self._botcont = botcont
		
	def __getattr__(self, name):
		if name in self.__dict__: return getattr(self, name)
		return getattr(self._botcont, name)
	
	# I think say should act as like a "reply" sending message back to whatever
	#  send it, be it channel or user
	def say(self, msg):
		if self.event.isPM():
			self.msg(self.event.nick, msg)
		else:
			self.msg(self.event.channel, msg)
			
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
