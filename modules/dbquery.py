#run db query
from util import Mapping

def dbquery(event, bot):
	if bot.isadmin():
		query = event.argument
		bot.say("Running: %s" % query)
		try:
			result = bot.dbQuery(query)
		except Exception as e:
			return bot.say("Error with query: %s" % e)
		
		if not result:
			return bot.say("No error, but nothing to display.")
		print "GOOD"
		#good
		for row in result:
			nrow = []
			for key in row.keys():
				nrow.append((key, row[key]))
			bot.say(repr(nrow))

	else:
		bot.say("uwish.")

mappings = (Mapping(command="dbquery", function=dbquery),)
