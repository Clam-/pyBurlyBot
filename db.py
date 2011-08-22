from threading import Thread
try:
	from pysqlite2 import dbapi2 as sqlite3
except:
	import sqlite3
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
		#just to see if we can open the file
		dbcon = sqlite3.connect(join("data", "bbm.db"))
		dbcon.close()
		self.incoming = incoming
		
	def run(self):
		dbcon = sqlite3.connect(join("data", "bbm.db"))
		dbcon.row_factory = sqlite3.Row
		running = True
		while running:
			query = self.incoming.get()
			try:
				if query == "STOP":
					break
				# ("select stuff where name_last=? and age=?", (who, age))
				params = ()
				if len(query) == 3:
					query, returnq, params = query
				elif len(query) == 2:
					query, returnq = query
				else:
					raise Exception("ValueError", "Too many or too few query arguments. %s" % len(query))
				returnq.put(("SUCCESS", dbcon.execute(query, params).fetchall()))
			except Exception as e1:
				try:
					returnq.put(("ERROR", e1))
				except Exception as e2:
					print "WARNING: SOME MODULE IS SENDING BAD THINGS: %", query
					print "EXCEPTION 1 IS: %s" % e1
					print "EXCEPTION 2 IS: %s" % e2
		print "SHUTTING DOWN DB THREAD"
		dbcon.commit()
		dbcon.close()
	# how should we deal with commits and stuff, can you even commit with execute? 
	# You can if you change transactional mode. Dont' really know which way should go