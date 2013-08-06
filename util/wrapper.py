# This seems like a bit of a waste, but it's difficult to implement this in Container
#  because of the reliance on event data.
# I don't really like creating one of these every dispatch.
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread

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
		return blockingCallFromThread(reactor, self._isadmin, module)
	
	#_isadmin bypasses the containers get*Option methods so that it
	# only makes 1 call in the reactor and not 2 (in the case of module)
	def _isadmin(self, module=None):
		if not self.event.nick: return None
		admins = self._botcont.settings.getOption("admins")
		if module:
			madmins = self._botcont.settings.getModuleOption(module, "admins")
			if madmins:
				admins.extend(madmins)
		return self.event.nick in admins
