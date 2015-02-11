# urbandictionary module

from util import Mapping

from textwrap import wrap as textwrap, dedent
from json import load as jsonload
from urllib import urlopen, quote as urlquote
from util.irctools import bold

DEFINITION_LENGTH = 250
TOTAL_LENGTH = 325
API_URL = 'http://api.urbandictionary.com/v0/define?term='
RANDOM_URL = 'http://api.urbandictionary.com/v0/random'


def format_definition(json_obj):
	""" Format an API-provided JSON object for display"""
	word = json_obj['word']
	definition = dedent(json_obj['definition']).replace('\r\n', ' ')
	example = dedent(json_obj['example']).replace('\r\n', ' ')
	permalink = json_obj['permalink']

	parts = textwrap(definition, DEFINITION_LENGTH)
	definition = parts[0]
	if len(parts) > 1:
		definition += ' [...]'

	parts = textwrap(example, TOTAL_LENGTH - len(definition))
	example = parts[0]
	if len(parts) > 1:
		example += ' [...]'

	s = bold(word) + ': '
	if definition and not example:
		s += definition
	elif example and not definition:
		s += 'E.g. ' + example
	else:
		# U+2014 EM DASH
		s += definition + u' \u2014 e.g. ' + example

	return '%s (%s)' % (s, permalink)


def urbandictionary(event, bot):
	""" urbandictionary [TERM]. Searches Urban Dictionary for TERM if supplied.
	Otherwise a random definition will be displayed."""
	if not event.argument:
		json_obj = jsonload(urlopen(RANDOM_URL))
	else:
		json_obj = jsonload(urlopen(API_URL + urlquote(event.argument)))
		if not json_obj['list']:
			return bot.say("No definition found for '%s'." % bold(event.argument))

	return bot.say(format_definition(json_obj['list'][0]))

mappings = (Mapping(command=("urbandictionary", "urband", "ud"), function=urbandictionary),)