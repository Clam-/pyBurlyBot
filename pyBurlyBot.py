#pyBurlyBot

from os.path import exists
from os import getcwdu
from os.path import join
from sys import exit, stdout
from argparse import ArgumentParser

# twisted imports
from twisted.python import log
from twisted.internet import reactor

#BurlyBot imports
from util.settings import Settings, ConfigException

if __name__ == '__main__':
	
	#TODO: make botdir an argument maybe
	Settings.botdir = getcwdu()
	# temporary logging
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
	parser.add_argument('config', nargs="?", metavar="CONFIGFILE", default="BurlyBot.json")
	
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
		Settings.load()
	except ConfigException as e:
		print "Error:", e
		exit(2)
	
	Settings.initialize(logger=templog)
	
	# start reactor (which in a sense starts bot proper)
	reactor.run()
