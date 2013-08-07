#run db query
from util import Mapping
from util.db import DBQuery

def dbquery(event, bot):
	if bot.isadmin():
		query = event.input
		bot.msg(event.channel, "Running: %s" % query)
		result = DBQuery(query)
		if result.error:
			return bot.msg(event.channel, "Error in query: %s" % result.error)

		if not result.rows:
			return bot.msg(event.channel, "No error, but nothing to display.")
		print "GOOD"
		#good
		for row in result.rows:
			nrow = []
			for key in row.keys():
				nrow.append((key, row[key]))
			bot.msg(event.channel, repr(nrow))

	else:
		bot.msg(event.channel, "uwish.")

		
def init():
	return True

mappings = (Mapping(types=["privmsged"], command="dbquery", function=dbquery),)
