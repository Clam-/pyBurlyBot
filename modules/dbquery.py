#run db query
from util import Mapping
from settings import Settings
from Queue import Queue

def dbquery(event, botinst, db):
	if event.nick in Settings.getModuleOption("core", "admins", botinst.factory.server["name"]):

		results = Queue()
		db.put(("SELECT name FROM sqlite_master WHERE name='alias'", results))
		result = results.get()
		if result[0] == "SUCCESS":
			#good
			for row in result[1]:
				nrow = []
				for col in row:
					nrow.append((col))
				botinst.msg(event.channel, str(nrow))
		else:
			botinst.msg(event.channel, "Error in query: %s" % result[1])

	else:
		botinst.msg(event.channel, "uwish.")

		
def init(db):
	return True

mappings = (Mapping(type=["privmsg"], command="dbquery", function=dbquery),)
