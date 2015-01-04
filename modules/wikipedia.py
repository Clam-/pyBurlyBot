# wikipedia module. Built using 
# https://github.com/goldsmith/Wikipedia

# because of this I don't think it can be used for generic mediawikis?

from wikipedia import search, page
from util import functionHelp, Mapping

# Title - body <URL>
RESULT_RPL = u"{0} - {1} <%s>"
RESULT_RPL_SP = u"(SP: %s?) {0} - {1} <%s>"

def wiki(event, bot):
	""" wiki \x02searchterm\x02. Will search Wikipedia for \x02searchterm\x02. """
	if not event.argument: return bot.say(functionHelp(wiki))
	result = search(event.argument, results=1, suggestion=True)
	if not result[0]: 
		if result[1]: return bot.say("No results found. Did you mean \x02%s\x02?" % result[1])
		else: return bot.say("No results found.")
	
	p = page(result[0]) # use preload=True  when it's fixed: https://github.com/goldsmith/Wikipedia/issues/78
	content = p.content[:800].replace("\n", " ").replace("====", "").replace("===", "").replace("==", "")
	if result[1]:
		bot.say(RESULT_RPL_SP % (result[1], p.url), strins=[p.title, content], fcfs=True)
	else:
		bot.say(RESULT_RPL % p.url, strins=[p.title, content], fcfs=True)
	

mappings = (Mapping(command=("wiki", "w", "wikipedia"), function=wiki),)