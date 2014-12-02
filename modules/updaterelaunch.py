#updaterelaunch super update reload module

from subprocess import check_output

# git fetch
# git diff --name-status master origin/master
#M       stuff
#M       things/abc.txt
# git merge origin/master 
from util import Mapping, argumentSplit, functionHelp

### Modules should not import this! Unless they have a very good reason to.
from util.settings import Settings

### This is only something that modules that know what they are doing should do:
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
###

OPTIONS = {
	"git_path" : (unicode, "Path to git executable.", u"git"),
}

#TODO: This won't really play nice when running multiple bot processes at a time.
#	After the first bot process updates, the rest will think they are up-to-date.
#	This could be solved by storing modtimes of modules and core files at launch time and comparing them.
def update(event, bot):
	""" update will check for git update and restart bot if core files need updating. """
	if not bot.isadmin():
		bot.say("Good joke.")
		return

	gitpath = bot.getOption("git_path", module="updaterelaunch")
	if not gitpath:
		gitpath = "git"
		
	check_output([gitpath, "fetch"])
	changes = check_output([gitpath, "diff", "--name-status", "master", "origin/master"])
	print "CHANGES:", changes
	corechange = False
	modchange = False
	for line in changes.splitlines():
		if line.lstrip("M\t").startswith("modules/"):
			modchange = True
		elif line.endswith(".py"):
			corechange = True
	check_output([gitpath, "merge", "origin/master"])
	
	if corechange:
		print "RESTARTING BOT"
		#restart bot
		blockingCallFromThread(reactor, Settings.shutdown, True)
		
	elif modchange:
		#reload
		if bot.isModuleAvailable("core"):
			bot.getModule("core").reloadbot(event, bot)
		else:
			bot.say("Module(s) updated but can't reload. core module not available.")



#mappings to methods
mappings = (Mapping(command="update", function=update),)