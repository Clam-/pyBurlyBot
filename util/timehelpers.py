#timehelpers.py
from datetime import timedelta
from time import time

# some codes stolen from here 
# http://stackoverflow.com/questions/2119472/convert-a-timedelta-to-days-hours-and-minutes

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
			
	
	
	