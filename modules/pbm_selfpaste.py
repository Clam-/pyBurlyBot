# selfpaste
# *NIX ONLY. (Unless you code up the file inode part for the win32 side...)

# used hashid because lazy

# TODO: probably not very secure. Probably vunerable to 100 JS injection things.

# need cron file that cleans up stale things that's run from cron

from tempfile import NamedTemporaryFile
from os.path import exists, isdir, join
from os import chmod, makedirs, stat, rename
from errno import EEXIST
from re import compile as recompile, UNICODE, IGNORECASE
from stat import S_IRUSR, S_IWUSR, S_IRGRP, S_IWGRP, S_IROTH
from cgi import escape
from urllib import unquote

from hashids import Hashids
hashids = Hashids()

from util import URLREGEX

PROVIDES = ("paste",)

OPTIONS = {
	"wwwroot" : (unicode, "Web directory location for storing pastes.", u"data/pastes/"),
	"url_prefix" : (unicode, "Prefix of the webfacing URL. e.g. 'http://domain.com/paste/'", u"http://localhost/pastepls"),
}

# tempfile.NamedTemporaryFile  dir= module/server path for www. prefix=tmp
# after file has been got, get it's inode number, write to file, then mode to hex(inode)

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8" />
	<title>%s</title>
	<link href='http://fonts.googleapis.com/css?family=Oxygen+Mono' rel='stylesheet' type='text/css'>
	<link rel="stylesheet" href="style/style.css">
</head>
<body>
<h3>%s</h3>
%s
</body>
</html>
"""

#Borrowed from helpers.coerceToUnicode
# TODO: I don't think this is actually needed.
ENCODINGS = ("utf-8", "sjis", "latin_1", "gb2312", "cp1251", "cp1252",
	"gbk", "cp1256", "euc_jp")
def decodeURL(u):
	u = unquote(u)
	if isinstance(u, unicode): return u
	for enc in ENCODINGS:
		try:
			return u.decode(enc)
		except UnicodeDecodeError:
			continue
	u = u.decode("utf-8", "replace")

# TODO: Do we need to define some sort of 'typical paste API'?
def paste(s, bot=None, title="BurlyBot paste", **kwargs):
	assert(bot is not None)
	wwwroot = bot.getOption("wwwroot", module="pbm_selfpaste")
	urlprefix = bot.getOption("url_prefix", module="pbm_selfpaste")
	assert(wwwroot and urlprefix)
	if not exists(wwwroot):
		try: makedirs(wwwroot)
		except OSError as e:
			if e.errno != EEXIST:
				return "PASTE ERROR: Cannot access wwwroot"
		
	tempfile = NamedTemporaryFile(mode='w+b', dir=wwwroot, delete=False)
	
	nf = "%s.%%s" % hashids.encode(stat(tempfile.name).st_ino)
	if "http" in s:
		# linkify stuff.
		# more tedious than I thought it would be... process each line, and cut out the surrounding nonlink text to escape
		title = escape(title)
		lastend = 0
		parts = []
		for match in URLREGEX.finditer(s):
			mstart, mend = match.span()
			parts.append(escape(s[lastend:mstart]))
			m = match.group()
			#ms = m.split("://", 1)
			# Assume generated URLs are already encoded properly, only need to htmlencode them
			parts.append('<a href="%s">%s</a>' % (escape(m), escape(decodeURL(m))))
			lastend = mend
		parts.append(escape(s[lastend:]))
		s = TEMPLATE % (title, title, "".join(("<p>%s</p>" % x for x in "".join(parts).split("\n"))))
		nf = nf % "html"
	else:
		nf = nf % "txt"
	tempfile.write(s.encode("utf-8"))
	tempfile.close()
	chmod(tempfile.name, S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP|S_IROTH) # 664
	rename(tempfile.name, join(wwwroot, nf))
	return "%s/%s" % (urlprefix.rstrip("/"), nf)
	
	
def init(bot):
	# TODO: maybe check if wwwroot is writable?
	return True
