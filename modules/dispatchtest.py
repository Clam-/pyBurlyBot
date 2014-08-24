#sample module
from re import compile as recompile
from util import Mapping

def test_things(event, botinst):
	print "%s Dispatched.  Prefix: '%s' Params: '%s'" % (event.type, event.prefix, event.params)

#mappings to methods
mappings = (Mapping(types=["privmsged", "NOTICE",
	"RPL_WELCOME", "JOIN", "PART", "MODE", "noticed", "NICK", "KICK", "TOPIC", "RPL_TOPIC", "RPL_NOTOPIC", "RPL_ENDOFMOTD",
	"RPL_NAMREPLY", "RPL_ENDOFNAMES", "RPL_YOURHOST", "042"], function=test_things),)
