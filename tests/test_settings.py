from os import getcwdu, remove, fsync
from os.path import join, abspath
from tempfile import NamedTemporaryFile

from twisted.trial.unittest import TestCase

from pyBBM.pyBBM import BBMBot
from pyBBM.util.settings import KEYS_MAIN, \
	SettingsBase, Settings

from pyBBM.tests import TestException

SETTINGS_TEST1 = """{
	"nick": "aaaaa",
	"nicksuffix": "^",
	"commandprefix": "&",
	"modules": [
		"module1",
		"module2",
		"module3"
	],
	"datadir": "testdir",
	"datafile": "test.db",
	"console" : false,
	"servers": [
		{
			"serverlabel": "server1",
			"host": "irc.server1.net",
			"port": "9999",
			"channels": [
				"#channel1",
				"#channel2"
			]
		},
		{
			"serverlabel": "server2",
			"host": "irc.server2.com",
			"port": 2222,
			"allowmodules" : ["module2"],
			"denymodules" : ["module1"]
		},
		{
			"serverlabel": "server3",
			"host": "irc.server3.biz",
			"port": "6666",
			"channels": [
				["#channel1", "password1"],
				["#channel2", "password2"],
				"#channel3"
			]
		}
	]
}"""


class SettingsTest(TestCase):
	def test_blank(self):
		Settings.configfile = None
		Settings.reload()
		for key in KEYS_MAIN:
			self.assertEqual(getattr(Settings, key), getattr(SettingsBase, key))
		# check servers
		self.assertEqual(len(Settings.servers), 0)
			
	def test_fixed(self):
		#create config file
		nt = NamedTemporaryFile(delete=False)
		nt.file.write(SETTINGS_TEST1)
		nt.file.flush()
		fsync(nt.file.fileno())
		config = nt.name
		nt.file.close()
		Settings.configfile = config
		Settings.reload()
		self.assertEqual(Settings.nick, "aaaaa")
		self.assertEqual(Settings.nicksuffix, "^")
		self.assertEqual(Settings.commandprefix, "&")
		self.assertEqual(Settings.modules, ["module1", "module2", "module3"])
		self.assertEqual(Settings.datadir, "testdir")
		self.assertEqual(Settings.datafile, "test.db")
		self.assertEqual(Settings.console, False)
		for serverlabel in Settings.servers:
			server = Settings.servers[serverlabel]
			if serverlabel == "server1":
				self.assertEqual(serverlabel, "server1")
				self.assertEqual(server.host, "irc.server1.net")
				self.assertEqual(server.port, "9999")
				self.assertEqual(server.channels, [("#channel1",), ("#channel2",)])
			elif serverlabel == "server2":
				self.assertEqual(serverlabel, "server2")
				self.assertEqual(server.host, "irc.server2.com")
				self.assertEqual(server.port, 2222)
				self.assertEqual(server.channels, [])
				self.assertEqual(server.allowmodules, set(["module2"]))
				self.assertEqual(server.denymodules, set(["module1"]))
			elif serverlabel == "server3":
				self.assertEqual(serverlabel, "server3")
				self.assertEqual(server.host, "irc.server3.biz")
				self.assertEqual(server.port, "6666")
				self.assertEqual(server.channels, [("#channel1", "password1"), ("#channel2", "password2"), 
					("#channel3",)])
			else:
				raise TestException("This shouldn't happen unless test is broken")
		
		remove(config)