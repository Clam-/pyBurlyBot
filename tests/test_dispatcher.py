from os import getcwdu, remove, fsync
from os.path import join, abspath

#Required path fudging for module space
import sys
botdir = abspath(join(getcwdu(), "pyBBM"))
sys.path.insert(0,botdir)

from twisted.trial.unittest import TestCase

from pyBBM.pyBBM import BBMBot
from pyBBM.util.settings import KEYS_MAIN, Settings
from pyBBM.util.dispatcher import Dispatcher

from pyBBM.tests import TestException
Settings.botdir = botdir

class DispatcherTest(TestCase):
	# silly but since this is my first test suite, no hate.
	def test_initial(self):
		Settings.reload()
		self.assertEqual(Dispatcher.hostmap, {})
		self.assertEqual(Dispatcher.modules, [])
		self.assertEqual(Dispatcher.hostwaitmap, {})
	
	def test_reloaded(self):
		Dispatcher.reload()
		