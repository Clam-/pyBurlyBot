from os import getcwdu, remove, fsync
from os.path import join, abspath

#Required path fudging for module space
import sys
botdir = abspath(join(getcwdu(), "pyBurlyBot"))
sys.path.insert(0,botdir)

from twisted.trial.unittest import TestCase

from pyBurlyBot.pyBurlyBot import BurlyBot
from pyBurlyBot.util.settings import KEYS_MAIN, Settings
from pyBurlyBot.util.dispatcher import Dispatcher

from pyBurlyBot.tests import TestException
Settings.botdir = botdir

# TODO: HORRIBLY OUTDATED
class DispatcherTest(TestCase):
	# silly but since this is my first test suite, no hate.
	def test_initial(self):
		#~ Settings.reload()
		#~ self.assertEqual(Dispatcher.hostmap, {})
		#~ self.assertEqual(Dispatcher.modules, [])
		#~ self.assertEqual(Dispatcher.hostwaitmap, {})
		pass
	
	def test_reloaded(self):
		pass
		