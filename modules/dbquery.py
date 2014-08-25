#run db query
from util import Mapping
from util.db import DBQuery

def dbquery(event, bot):
	if bot.isadmin():
		query = event.input
		bot.say("Running: %s" % query)
		result = DBQuery(query)
		if result.error:
			return bot.say("Error in query: %s" % result.error)

		if not result.rows:
			return bot.say("No error, but nothing to display.")
		print "GOOD"
		#good
		for row in result.rows:
			nrow = []
			for key in row.keys():
				nrow.append((key, row[key]))
			bot.say(repr(nrow))

	else:
		bot.say("uwish.")

mappings = (Mapping(types=["privmsged"], command="dbquery", function=dbquery),)
