"""
butt.py - A (poor) python port of buttbot:
https://code.google.com/p/buttbot/

This is ported almost directly from old BBM

TODO:
- Tie in configurable variables
- Look into preventing rand_butt from being called on a dispatched command
"""

from re import compile as re_compile
from util import Mapping
from time import sleep
from random import randint, shuffle
try:
	from hyphenate import hyphenate_word
except ImportError:
	raise ImportError('butt.py needs Need TeX Hyphenate: http://nedbatchelder.com/code/modules/hyphenate.py')


BUTT_RATE = 500 # 1 in 501, this was old rate

STOPWORDS = ('a', 'an', 'and', 'or', 'but', 'it', 'is',
'its', 'It\'s', 'it\'s', 'the', 'of', 'you', 'I', 'i',
'your')

RE_STOPWORDS = re_compile(r'^([\d\W+]+$|' + '|'.join(STOPWORDS) + ')$')
RE_SPLITPUNCTUATION= re_compile(r'^([^A-Za-z]*)(.*?)([xXsS]?[^A-Za-z]*)$')


def butt(event, bot):
	if not event.argument:
		bot.say("butt what?")
	else:
		bot.say(buttify(event.argument))


def rand_butt(event, bot):
	msg = event.msg
	if not msg or not len(msg) > 20: return
	if randint(0, BUTT_RATE) != 0: return
	result = buttify(msg)
	# No butt occurred
	if result == msg: return
	sleep(randint(2,8))
	bot.say(result)


def buttify(istr):
	"""Take a string and buttify it."""
	words = istr.split()
	basewords = list(words)
	repetitions = len(words) / 8 + 1

	# Sort list by word length
	words.sort(lambda x,y: cmp(len(x), len(y)), reverse=True)
	# Remove stop words
	words = _remove_stop_words(words)
	# create weighted index array of words by length
	indices = _weighted_indices(words)
	if indices: shuffle(indices)

	for i in range(0, repetitions):
		try: index = indices.pop(i)
		except IndexError: break

	for i in range(0, len(basewords)):
		if basewords[i] == index:
			basewords[i] = _buttsub(basewords[i])
			newindices = []
			for word in indices:
				if word != index:
					newindices.append(word)
			break

	return ' '.join(basewords)


def _buttsub(word):
	lp, actual_word, rp = RE_SPLITPUNCTUATION.match(word).groups()
	if not actual_word: return word

	x = 0
	points = [0]
	boilerplate = hyphenate_word(actual_word)
	for i in range(0, len(boilerplate) - 1):
		x += len(boilerplate[i])
		points.append(x)
	points.append(len(actual_word))

	length = len(points)
	try: replace = randint(0, length - 2) # length - 1 - int(rand(0, length ** factor) ** (1 / float(factor)))
	except ValueError: replace = 0
	points.append(len(actual_word))
	l = points[replace]
	r = points[replace + 1] - l
	while (actual_word[l + r: l + r + 1]) == 't':
		r += 1
	while l > 0 and actual_word[l - 1] == 'b': l -= 1
	sub = actual_word[l:l+r]
	butt = 'butt'
	if not len(sub):
		sub = actual_word
		l = 0
		r = len(sub)
	if sub.isupper():
		butt = 'BUTT'
	elif sub[0].isupper():
		butt = 'Butt'

	actual_word = actual_word[:l] + butt + actual_word[l+r:]
	return lp + actual_word + rp


def _remove_stop_words(sortedlist):
	newlist = []
	for word in sortedlist:
		if not RE_STOPWORDS.search(word):
			newlist.append(word)
	return newlist


def _weighted_indices(sortedlist):
	weight = len(sortedlist)
	stack = []
	for word in sortedlist:
		for i in range(0, weight**2):
			stack.append(word)
		weight -= 1
	return stack


mappings = (Mapping(command="butt", function=butt),
			Mapping(types=["privmsged"], function=rand_butt))
