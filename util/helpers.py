#timehelpers.py
from datetime import timedelta
from time import time
from codecs import lookup
from operator import itemgetter
from shlex import shlex
from StringIO import StringIO
from inspect import getdoc
from re import compile as compile_re

# extend shlex to implement slightly modified parser to treat all "nonhandled" characters
# as "wordchars". Should mean it parses unicode and symbols as words.
# read_token is taken almost verbatim from origin and only modified slightly.
class newshlex(shlex):
	def __init__(self, *args, **kwargs):
		shlex.__init__(self, *args, **kwargs)
		#self.debug = 5
		
	def read_token(self):
		quoted = False
		escapedstate = ' '
		while True:
			nextchar = self.instream.read(1)
			if nextchar == '\n':
				self.lineno = self.lineno + 1
			if self.debug >= 3:
				print "shlex: in state", repr(self.state), \
					"I see character:", repr(nextchar)
			if self.state is None:
				self.token = ''        # past end of file
				break
			elif self.state == ' ':
				if not nextchar:
					self.state = None  # end of file
					break
				elif nextchar in self.whitespace:
					if self.debug >= 2:
						print "shlex: I see whitespace in whitespace state"
					if self.token or (self.posix and quoted):
						break   # emit current token
					else:
						continue
				elif nextchar in self.commenters:
					self.instream.readline()
					self.lineno = self.lineno + 1
				elif self.posix and nextchar in self.escape:
					escapedstate = 'a'
					self.state = nextchar
				elif nextchar in self.quotes:
					if not self.posix:
						self.token = nextchar
					self.state = nextchar
				elif self.whitespace_split:
					self.token = nextchar
					self.state = 'a'
				else:
					self.token = nextchar
					if (self.posix and quoted):
						break   # emit current token
					else:
						self.state = 'a' # treat all characters like wordchars
						continue
			elif self.state in self.quotes:
				quoted = True
				if not nextchar:      # end of file
					if self.debug >= 2:
						print "shlex: I see EOF in quotes state"
					# XXX what error should be raised here?
					raise ValueError, "No closing quotation"
				if nextchar == self.state:
					if not self.posix:
						self.token = self.token + nextchar
						self.state = ' '
						break
					else:
						self.state = 'a'
				elif self.posix and nextchar in self.escape and \
						self.state in self.escapedquotes:
					escapedstate = self.state
					self.state = nextchar
				else:
					self.token = self.token + nextchar
			elif self.state in self.escape:
				if not nextchar:      # end of file
					if self.debug >= 2:
						print "shlex: I see EOF in escape state"
					# XXX what error should be raised here?
					raise ValueError, "No escaped character"
				# In posix shells, only the quote itself or the escape
				# character may be escaped within quotes.
				if escapedstate in self.quotes and \
						nextchar != self.state and nextchar != escapedstate:
					self.token = self.token + self.state
				self.token = self.token + nextchar
				self.state = escapedstate
			elif self.state == 'a':
				if not nextchar:
					self.state = None   # end of file
					break
				elif nextchar in self.whitespace:
					if self.debug >= 2:
						print "shlex: I see whitespace in word state"
					self.state = ' '
					if self.token or (self.posix and quoted):
						break   # emit current token
					else:
						continue
				elif nextchar in self.commenters:
					self.instream.readline()
					self.lineno = self.lineno + 1
					if self.posix:
						self.state = ' '
						if self.token or (self.posix and quoted):
							break   # emit current token
						else:
							continue
				elif self.posix and nextchar in self.quotes:
					self.state = nextchar
				elif self.posix and nextchar in self.escape:
					escapedstate = 'a'
					self.state = nextchar
				elif nextchar in self.wordchars or nextchar in self.quotes \
						or self.whitespace_split:
					self.token = self.token + nextchar
				else: # treat all characters like wordchars
					self.token = self.token + nextchar
		result = self.token
		self.token = ''
		if self.posix and not quoted and result == '':
			result = None
		if self.debug > 1:
			if result:
				print "shlex: raw token=" + repr(result)
			else:
				print "shlex: raw token=EOF"
		if quoted:
			return result[1:-1]
		return result

# adapted http://stackoverflow.com/a/2119512
def days_hours_minutes(td):
	return td.days, td.seconds//3600, (td.seconds//60)%60, td.seconds % 60

def pluralize(term, num):
	if num > 1: return term + "s"
	else: return term
	
#distance_of_time_in_words hardcoded granularity
def distance_of_time_in_words(fromtime, totime=None, suffix="ago"):
	if not totime:
		totime = time()
	past = True
	diff = totime-fromtime
	if diff < 0:
		past = False
		diff = abs(diff)
	if diff < 20:
		if past: return "just a moment %s" % suffix
		else: return "in just a moment"
	
	td = timedelta(seconds=diff)
	days, hours, minutes, seconds = days_hours_minutes(td)
	
	chunks = []
	if hours or days or minutes > 10:
		terms = (("day", days), ("hour", hours), ("minute", minutes))
	else:
		terms = (("day", days), ("hour", hours), ("minute", minutes), ("second", seconds))
	for term, value in terms:
		if value:
			chunks.append((value, pluralize(term, value)))
	
	s = ""
	while chunks:
		s += "%s%s" % chunks.pop(0)
		if len(chunks) >= 2:
			s += ", "
		elif len(chunks) == 1:
			s += " and "
		else:
			if past: s += " %s" % suffix
			else:
				s = "in " + s
	return s
			
#isIterable (the tuple or list kind of iterable)
# maybe there is a more apt name
def isIterable(i):
	return isinstance(i, tuple) or isinstance(i, list)
	
def processHostmask(h):
	if h:
		try:
			nick, ident = h.split('!', 1)
			ident, host = ident.split('@', 1)
		except ValueError:
			pass
		else:
			return (nick, ident, host)
	return (None, None, None)

# Useful thing http://stackoverflow.com/a/8528866
# This may return incorrectly decoded string because naive
ENCODINGS = ("utf-8", "sjis", "latin_1", "gb2312", "cp1251", "cp1252",
	"gbk", "cp1256", "euc_jp")
def coerceToUnicode(s, enc=None):
	if enc:
		try: return s.decode(enc)
		except UnicodeDecodeError: pass
	for enc in ENCODINGS:
		try:
			return s.decode(enc)
		except UnicodeDecodeError:
			continue
	s = s.decode("utf-8", "replace")
	print "Warning, unknown coded character encounted in %s" % s
	return s
		
def processListReply(params):
	channel = params[1]
	mask = params[2]
	nick, ident, host = processHostmask(params[3])
	t = params[4]
	return channel, mask, nick, ident, host, t, params[3]

# TODO: This seems pretty clunky. Maybe revisit/refactor it in future...	
class PrefixMap(object):
	def __init__(self, prefixiter):
		self.loadfromprefix(prefixiter)
		
	def loadfromprefix(self, prefixiter):
		prefixes = []
		opfixes = []
		opcmds = []
		foundop = False
		foundvoice = False
		usermodemap = {}
		voicefixes = []
		voicecmds = []
		for cmd, p, num in sorted(((cmd, p, num) for cmd, (p, num) in prefixiter), key=itemgetter(2)):
			#('~', 0)
			# identify index of traditional op (@) and class everything under "op"
			# also identify index of voice and likewise
			prefixes.append(p)
			if not foundop:
				opfixes.append(p)
				opcmds.append(cmd)
			elif not foundvoice:
				voicefixes.append(p)
				voicecmds.append(cmd)
			if p == "@":
				foundop = True
			elif p == "v":
				foundvoice = True
			usermodemap[cmd] = p
		
		self.opprefixes = "".join(opfixes)
		self.opcmds = "".join(opcmds)
		self.nickprefixes = "".join(prefixes)
		self.usermodemap = usermodemap
		self.voiceprefixes = "".join(voicefixes)
		self.voicecmds = "".join(voicecmds)


# Simple command parse and return (command, argument)
# split arguments in to [nargs] number of elements in the case of nargs > 1 else argument will be singular string
# if pad=False: if len(arguments) < nargs return None as argument, 
# else pad missing arguments with None
def commandSplit(s, nargs=1, pad=True):
	command = ""
	if s:
		command = s.split(None, 1)
		if len(command) > 1:
			if nargs > 1:
				a = argumentSplit(command[1], nargs, pad)
				if a:
					return (command[0], a)
				else:
					return (command[0], None)
			else:
				return command
		else:
			if pad and nargs > 1:
				return command[0], (None,) * nargs
			return command[0], None
	return (None, None)

# like commandSplit, this is only for splitting arguments up
# except will return empty tuple in the case of nargs < len(arguments) if pad is false
def argumentSplit(s, nargs, pad=True):
	if s:
		s = newshlex(StringIO(s)) # use non-C StringIO for (somewhat) unicode support?
		i = 0
		args = []
		while (i < nargs -1) or nargs == -1: # allows to split entire string
			tok = s.get_token()
			if not tok: break
			args.append(tok)
			i += 1
		rest = s.instream.read().strip() 	#TODO: should this really be stripping here? Without strip:
		if rest:							# >>> argumentSplit('one "two three" four', 3)
			args.append(rest)				# ['one', 'two three', ' four']
			i += 1
		if pad:
			while i < nargs:
				args.append(None)
				i += 1
		return args
	else:
		if pad: return [None]*nargs
		else: return ()

# TODO: add more outgoing things here for length calculation		
commandlength = {
	"sendmsg" : 'PRIVMSG %s :',
}


# Complicated method. Will split a unicode string to desires length without returning
# malformed unicode strings.
# Will return a list of (stringsegment, length of encoding) tuples.
def splitEncodedUnicode(s, length, encoding="utf-8", n=1):
	if length < 1: return [("", 0)]
	es = s.encode(encoding)
	le = len(es)
	if le <= length:
		return [(s, le)]
	else:
		splits = []
		ib = 0 # start of segment
		# UTF-8 makes this somewhat easy
		if lookup(encoding).name == "utf-8":
			while ib < le and len(splits) < n:
				ie = ib+length # end of segment
				if ie >= le: 
					splits.append(es[ib:ie])
					break
				c = es[ie]
				#check for unicode character start byte, and backtrack if not found
				while (0b10000000 & ord(c) != 0) and (0b11000000 & ord(c) != 0b11000000) and ie > 0:
					ie -= 1
					c = es[ie]
				splits.append(es[ib:ie])
				if ib == ie: 
					# in rare case that a character can't fit, skip it.
					ie += 1
					try:
						c = es[ie]
						while (0b10000000 & ord(c) != 0) and (0b11000000 & ord(c) != 0b11000000):
							ie += 1
							c = es[ie]
					except IndexError: 
						break # break if end of encoded string is reached.
				ib = ie
			splits = [(s.decode("utf-8"), len(s)) for s in splits] #TODO: this double conversion seems kind of wasteful
			# it might be faster to calc all the endchar points first and then translate back.
		else:
			# not as bad as I thought it would be, but pretty bad
			sl = len(s) # length of original string
			while ib < sl and len(splits) < n:
				ie = ib+length 				# end of segment
				ss = s[ib:ie] 				# original string spliced
				sse = ss.encode(encoding) 	# encoding of that splice
				le = len(sse) 				# length of encoded splice
				while le > length:
					ie -= int(round((le - length) / 1.8)) # trim 1.8 times the extra length, seemed like good compromise
					ss = s[ib:ie]
					sse = ss.encode(encoding)
					le = len(sse)
				splits.append((ss, le))
				ib = ie
		return splits

# retrieve help for function f. sub will provide help for that sub command
def functionHelp(f, sub=None):
	doc = getdoc(f)
	if doc:
		docs = doc.replace("\n", " ").split("|")
		if not sub:
			return docs[0]
		else:
			for subdoc in docs:
				try: 
					if subdoc.split(" ", 1)[1].startswith(sub):
						return subdoc
				except IndexError: pass
			return docs[0]
	else:
		return ""

MIRC_CONTROL_BOLD = '\x02'
MIRC_CONTROL_COLOR = '\x03'
MIRC_CONTROL_UNDERLINE = '\x1f'
MIRC_CONTROL_ITALICIZE = '\x1d'
MIRC_CONTROL_CLEARFORMATTING = '\x0f'


# http://www.mirc.com/colors.html
MIRC_COLORS = {
	"white": 0,
	"black": 1,
	"blue": 2, "navy": 2,
	"green": 3,
	"red": 4,
	"brown": 5,	"maroon": 5, "javad": 5, #Ahaheuaheuaehu
	"purple": 6,
	"orange": 7, "olive": 7,
	"yellow": 8,
	"light green": 9, "lime": 9,
	"teal": 10,	"green/blue": 10, "green/blue cyan": 10,
	"light cyan": 11, "cyan": 11, "aqua": 11,
	"light blue": 12, "royal": 12,
	"pink": 13,	"light purple": 13,	"fuschia": 13,
	"grey": 14,	"cloud": 14,
	"light grey": 15, "silver": 15
}



# TODO split to irc specific utils?
def colorize(s, fg=None, bg=None):
	if fg:
		fg_orig = fg
		try:
			fg = int(fg)
		except ValueError:
			try:
				fg = MIRC_COLORS[fg.lower()]
			except (ValueError, KeyError):
				fg = None
		finally:
			if not fg or fg < 0 or fg > 15:
				raise ValueError('Invalid color:  %s' % fg_orig)
	if bg:
		bg_orig = bg
		try:
			bg = int(bg)
		except ValueError:
			try:
				bg = MIRC_COLORS[bg.lower()]
			except (ValueError, KeyError):
				bg = None
		finally:
			if not bg or bg < 0 or bg > 15:
				raise ValueError('Invalid color:  %s' % bg_orig)
	if fg and bg:
		color_s = '%s,%s' % (fg, bg)
	elif fg:
		color_s = '%s' % fg
	elif bg:
		# mIRC's behavior here is to honor the BG color if the FG color is any
		# (valid or not) 2 digit number.  If the FG color is invalid the BG
		# color will display without modifying the FG color, oddly.
		# So we'll just use 99 in these cases to avoid modifying the FG color
		color_s = '99,%s' % bg
	return MIRC_CONTROL_COLOR + color_s + s + MIRC_CONTROL_COLOR

def bold(s):
	return MIRC_CONTROL_BOLD + s + MIRC_CONTROL_BOLD

def underline(s):
	return MIRC_CONTROL_UNDERLINE + s + MIRC_CONTROL_UNDERLINE

def italicize(s):
	return MIRC_CONTROL_ITALICIZE + s + MIRC_CONTROL_ITALICIZE


RE_COLOR_CODE = r'(\x03(([0-9]{1,2})(,[0-9]{1,2})?|[0-9]{2},[0-9]{1,2}))+'
RE_TRAILING_COLOR_CODE = compile_re(RE_COLOR_CODE + r'$')
RE_COLOR_CODE = compile_re(RE_COLOR_CODE)

# Regarding mIRC color codes: Any valid FG or BG value will cause the text color
# to be modified.  All of the following will do something:
# '\x0399,00', '\x0300,99', '\x0303,3238' (will display '38' in green text)
def escape_control_codes(s):
	'''
	Append the appropriate mIRC control character to string s to escape the
	active string control codes, or append MIRC_CONTROL_CLEARFORMATTING (\x0f)
	if multiple control codes are in play.  e.g.:

	escape_control_codes('\x02\x1d\x0315TEST STRING')
	>>> '\x02\x1d\x0315TEST STRING\x0f'
	escape_control_codes('\x02TEST \x1fSTRI\x02NG')
	>>> '\x02TEST \x1fSTRI\x02NG\x1f'
	'''
	s_len = len(s)
	# Pop control characters off of the right side since we'll be escaping them anyways
	s = s.rstrip(MIRC_CONTROL_BOLD + MIRC_CONTROL_UNDERLINE +
	MIRC_CONTROL_ITALICIZE + MIRC_CONTROL_COLOR + MIRC_CONTROL_CLEARFORMATTING)
	s = RE_TRAILING_COLOR_CODE.sub('', s)
	control_tracking = set()
	for index, c in enumerate(s):
		if c in (MIRC_CONTROL_BOLD,	MIRC_CONTROL_UNDERLINE,	MIRC_CONTROL_ITALICIZE):
			if c in control_tracking:
				control_tracking.remove(c)
			else:
				control_tracking.add(c)
		elif c == MIRC_CONTROL_COLOR:
			fg_color_num = ''
			bg_color_num = ''
			# Peek ahead to see if the color code is valid ('0' - '15')
			if (index + 1) < s_len and s[index + 1].isdigit():
				fg_color_num += s[index + 1]
				if (index + 2) < s_len and s[index + 2].isdigit():
					fg_color_num += s[index + 2]
			if fg_color_num:
				# Valid FG color, color mode activated, we can bail out for this iteration here
				if 0 <= int(fg_color_num) <= 15:
					control_tracking.add(c)
					continue
				# Invalid FG color, peek farther (if we can) to check for a valid BG color
				elif (index + 4) < s_len and s[index + 3] == ',' and s[index + 4].isdigit():
					bg_color_num += s[index + 4]
					if (index + 5) < s_len and s[index + 5].isdigit():
						bg_color_num += s[index + 5]
			# Valid BG color, regardless of FG color this will have an impact on color
			if bg_color_num and 0 <= int(bg_color_num) <= 15:
					control_tracking.add(c)
			# Invalid FG and BG color, so it'll cancel any active colors, stop tracking.
			elif c in control_tracking:
				control_tracking.remove(c)
		elif c == MIRC_CONTROL_CLEARFORMATTING:
				control_tracking.clear()
	if len(control_tracking) > 1:
		s += MIRC_CONTROL_CLEARFORMATTING
	elif len(control_tracking) == 1:
		s += control_tracking.pop()
	return s

def AAA(s):
	return bold(underline(italicize(color('RED'))))

