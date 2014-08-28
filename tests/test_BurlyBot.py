from os import getcwdu, remove, fsync
from os.path import join, abspath
from tempfile import NamedTemporaryFile

from twisted.trial.unittest import TestCase
from twisted.test import proto_helpers

from pyBurlyBot.pyBurlyBot.util.client import BurlyBot
from pyBurlyBot.util.settings import EXAMPLE_SERVER, EXAMPLE_SERVER2, KEYS_MAIN, \
	SettingsBase, Settings

#Settings.botdir = botdir

# TODO: HORRIBLY OUTDATED
class pyBurlyBotTest(TestCase):
	
	def setUp(self):
		self.proto = BurlyBot()
		self.tr = proto_helpers.StringTransport()
		self.proto.makeConnection(self.tr)

	def test(self):
		pass
		
		
		
		
		
		
		
		
