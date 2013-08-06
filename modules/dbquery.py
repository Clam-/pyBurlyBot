#run db query
from util import Mapping, Settings
from util.db import DBQuery

def dbquery(event, botinst):
	if event.nick in Settings.getModuleOption("core", "admins", botinst.network):

		query = event.input
		botinst.msg(event.channel, "Running: %s" % query)
		result = DBQuery(query)
		if result.error:
			return botinst.msg(event.channel, "Error in query: %s" % result.error)

		if not result.rows:
			return botinst.msg(event.channel, "No error, but nothing to display.")
		print "GOOD"
		#good
		for row in result.rows:
			nrow = []
			for key in row.keys():
				nrow.append((key, row[key]))
			botinst.msg(event.channel, repr(nrow))

	else:
		botinst.msg(event.channel, "uwish.")

		
def init():
	return True

mappings = (Mapping(types=["privmsged"], command="dbquery", function=dbquery),)
