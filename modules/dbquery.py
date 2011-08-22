#run db query
from util import Mapping
from settings import Settings
from Queue import Queue

def dbquery(event, botinst, db):
	if event.nick in Settings.getModuleOption("core", "admins", botinst.servername):

		results = Queue()
		query = event.msg.lstrip(Settings.getOption("commandprefix", botinst.servername)+"dbquery")
		botinst.msg(event.channel, "Running: %s" % query)
		db.put((query, results))
		result = results.get()
		if result[0] == "SUCCESS":
			print "GOOD"
			#good
			for row in result[1]:
				nrow = []
				for key in row.keys():
					nrow.append((key, row[key]))
				botinst.msg(event.channel, repr(nrow))
				it = []
				for i in row:
					it.append(i)
				botinst.msg(event.channel, "Iter thing: %s" % repr(it))
		else:
			botinst.msg(event.channel, "Error in query: %s" % result[1])

	else:
		botinst.msg(event.channel, "uwish.")

		
def init(db):
	return True

mappings = (Mapping(type=["privmsg"], command="dbquery", function=dbquery),)
