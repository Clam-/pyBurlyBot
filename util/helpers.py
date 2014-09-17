#timehelpers.py
from datetime import timedelta
from time import time
from codecs import lookup
from operator import itemgetter

# adapted http://stackoverflow.com/a/2119512
def days_hours_minutes(td):
	return td.days, td.seconds//3600, (td.seconds//60)%60, td.seconds % 60

def pluralize(term, num):
	if num > 1: return term + "s"
	else: return term
	
#distance_of_time_in_words
def distance_of_time_in_words(fromtime, totime=None):
	if not totime:
		totime = time()
	past = True
	diff = totime-fromtime
	if diff < 0:
		past = False
		diff = abs(diff)
	if diff < 10:
		if past: return "Just a moment ago."
		else: return "In just a moment."
	
	td = timedelta(seconds=diff)
	days, hours, minutes, seconds = days_hours_minutes(td)
	
	chunks = []
	for term, value in (("day", days), ("hour", hours), ("minute", minutes), ("second", seconds)):
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
			if past: s += " ago."
			else: 
				s += "."
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
# split arguments in to [nargs] number of elements 
# only if number of arguments would equal nargs, otherwise return None argument
def commandSplit(s, nargs=1):
	command = ""
	if s:
		command = s.split(" ", 1)
		if len(command) > 1:
			if nargs > 1:
				a = command[1].split(" ", nargs)
				if len(a) != nargs:
					return (command[0], None)
				else:
					return (command[0], a)
			else:
				return command
		else:
			return command[0], None
	return (None, None)

# like commandSplit, this is only for splitting arguments up
def argumentSplit(s, nargs):
	if s:
		a = s.split(" ", nargs)
		if len(a) != nargs:
			return ()
		else:
			return a
	else:
		return ()

# TODO: add more outgoing things here for length calculation		
commandlength = {
	"sendmsg" : 'PRIVMSG %s :',
}


def splitEncodedUnicode(s, length, encoding="utf-8", n=1):
	if length < 1: return [""]
	le = len(s.encode(encoding))
	if le <= length:
		return [s]
	else:
		splits = []
		ib = 0 # start of segment
		# UTF-8 makes this somewhat easy
		if lookup(encoding).name == "utf-8":
			es = s.encode("utf-8")
			while ib < le and len(splits) < n:
				ie = ib+length # end of segment
				if ie >= le: 
					splits.append(es[ib:ie])
					break
				c = es[ie]
				#check for unicode character start byte, and backtrack if not found
				while (0b10000000 & ord(c) != 0) and (0b11000000 & ord(c) != 0b11000000):
					ie -= 1
					c = es[ie]
				splits.append(es[ib:ie])
				if ib == ie: 
					# in rare case that a character can't fit, skip it.
					ie += 1
					c = es[ie]
					while (0b10000000 & ord(c) != 0) and (0b11000000 & ord(c) != 0b11000000):
						ie += 1
						c = es[ie]
				ib = ie
			splits = [s.decode("utf-8") for s in splits] #TODO: this double conversion seems kind of wasteful
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
				splits.append(ss)
				ib = ie
		return splits
	

	