from threading import Thread
try:
	from pysqlite2 import dbapi2 as sqlite3
except:
	print "WUT"
#DB handler

from os.path import exists, join, isfile
from os import mkdir

class DBaccess(Thread):
	def __init__(self, incoming):
		Thread.__init__(self)
		if not exists("data"):
			mkdir("data")
		elif isfile("data"):
			raise IOError("data should not be file")
		self.dbcon = sqlite3.connect(join("data", "bbm.db"))
		self.dbcon.row_factory = sqlite3.Row
		self.incoming = incoming
		
	def run(self):
		running = True
		while running:
			query = self.incoming.get()
			if query == "STOP":
				break
			# ("select stuff where name_last=? and age=?", (who, age))
			if len(query) > 1:
				query, returnq, params = query
			else:
				query, returnq = query
			returnq.put(self.dbcon.execute(query, params))
	# how should we deal with commits and stuff, can you even commit with execute? 
	# You can if you change transactional mode. Dont' really know which way should go