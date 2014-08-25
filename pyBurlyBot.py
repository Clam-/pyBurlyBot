#pyBurlyBot

from os.path import exists
from os import getcwdu
from os.path import join
from sys import exit, stdout
from argparse import ArgumentParser

# twisted imports
from twisted.internet import reactor
try: 
	SSL = True
	from twisted.internet.ssl import ClientContextFactory
except:
	SSL = None
from twisted.python import log

#BurlyBot imports
from util.client import BurlyBotFactory
from util.settings import Settings, ConfigException
from util.container import Container
from util.db import DBQuery, dbcommit, setupDB
from util.timer import Timers

if __name__ == '__main__':
	
	#TODO: make botdir an argument maybe
	Settings.botdir = getcwdu()
	# initialize logging
	templog = log.startLogging(stdout)
	print "Starting pyBurlyBot, press CTRL+C to quit."
	
	parser = ArgumentParser(description="Internet bort pyBurlyBot", 
		epilog="pyBurlyBot requires a config file to be specified to run.")
	parser.add_argument("-c", "--create-config", action="store_true", dest="createconfig", 
		default=False, help="Creates example config. CONFIGFILE if specified else BurlyBot.json")
	parser.add_argument("-f", "--force", action="store_true", dest="force", 
		default=False, help="Force overwrite of existing config when creating config.")
	# CONSIDER: this could easily support multiple config files I guess
	#   but changing Settings to support this would be kind of intense I think.
	parser.add_argument('config', nargs="?", metavar="CONFIGFILE", default=None)
	
	args = parser.parse_args()
	
	# create-config
	if args.createconfig:
		if not args.config: args.config = "BurlyBot.json"
		print "Creating configuration..."
		if exists(args.config) and not args.force:
			print "Error: NEWCONFIGFILE (%s) exists. Use --force (-f) to force overwrite. Bailing." % args.config
			exit(1)
		Settings.configfile = args.config
		Settings.saveOptions()
		print "Done."
		exit(0)
		
	if args.config and exists(args.config):
		Settings.configfile = args.config
	else:
		print "Error: Settings file (%s) not found." % args.config
		exit(2)
	try:
		Settings.reload()
	except ConfigException as e:
		print "Error:", e
		exit(2)

	#setup log options
	if not Settings.console:
		templog.stop()
		log.startLogging(open(join(Settings.botdir, "BurlyBot.log"), 'a'), setStdout=False)
	# else:
		# log.startLogging(stdout)
	
	setupDB(join(Settings.botdir, Settings.datadir), Settings.datafile)
	DBQuery.dbThread.start()
	Settings.reloadDispatchers()
	#start dbcommittimer
	#def addtimer(cls, name, interval, f, kwargs={}, reps=None, startnow=False):
	Timers._addTimer("_dbcommit", 60*60, dbcommit, reps=-1) #every hour (60*60)
	
	# create factory protocol and application
	if Settings.servers:
		for server in Settings.servers.values():
			if server.ssl:
				if not SSL:
					print "Error: Cannot connect to '%s', pyOpenSSL not installed" % server.serverlabel
				else:
					reactor.connectSSL(server.host, server.port, BurlyBotFactory(server), ClientContextFactory())
			else:
				reactor.connectTCP(server.host, server.port, BurlyBotFactory(server))
		# run bot
		reactor.run()
	else:
		print "No servers to connect to. Bailing."
	
	#stop timers or just not care...
	Timers._stopall()
	DBQuery.dbQueue.put("STOP")
	DBQuery.dbThread.join()
