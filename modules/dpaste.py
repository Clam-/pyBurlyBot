#dpaste module

from urllib2 import urlopen, URLError
from urllib import urlencode

from traceback import print_exc

PROVIDES = ("paste",)

APIURL = "http://dpaste.com/api/v2/"

def paste(s, syntax="text", title="BurlyBot paste", poster="BurlyBot", expiry_days=1):
	data = {
		"title" : title.encode("utf-8"),
		"syntax" : syntax.encode("utf-8"),
		"poster" : poster.encode("utf-8"),
		"expiry_days" : expiry_days,
		"content" : s.encode("utf-8")
	}
	try: return urlopen(APIURL, urlencode(data)).geturl()
	except URLError, HTTPError: print_exc()
	return None
		