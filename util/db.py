from threading import Thread
from Queue import Queue
try:
	from pysqlite2 import dbapi2 as sqlite3
except:
	import sqlite3
#DB handler

from os.path import exists, join, isfile
from os import mkdir

class DBaccess(Thread):
	def __init__(self, incoming, datadir):
		Thread.__init__(self)
		self.datadir = datadir
		if not exists(self.datadir):
			mkdir(self.datadir)
		elif isfile(self.datadir):
			raise IOError("data should not be file")
		#just to see if we can open the file
		dbcon = sqlite3.connect(join(self.datadir, "bbm.db"))
		dbcon.close()
		self.incoming = incoming
		
	def run(self):
		dbcon = sqlite3.connect(join(self.datadir, "bbm.db"))
		dbcon.row_factory = sqlite3.Row
		running = True
		while running:
			query = self.incoming.get()
			try:
				if query == "STOP":
					break
				elif query == "COMMIT" or query == "COMMIT;":
					dbcon.commit()
					continue
				# ("select stuff where name_last=? and age=?", (who, age))
				query, params, returnq = query
				returnq.put(("SUCCESS", dbcon.execute(query, params).fetchall()))
			except Exception as e:
				returnq.put(("ERROR", e))
		print "SHUTTING DOWN DB THREAD"
		dbcon.commit()
		dbcon.close()
	# how should we deal with commits and stuff, can you even commit with execute? 
	# You can if you change transactional mode. Dont' really know which way should go

class DBQuery(object):
	dbQueue = None
	dbThread = None
	__slots__ = ('returnq', 'error', 'rows')
	
	def __init__(self, query=None, params=()):
		self.returnq = Queue()
		# For instanciating at the beginning of a bunch of if/else things
		if query:
			self.query(query, params)
	
	def query(self, query, params=()):
		self.error = None
		DBQuery.dbQueue.put((query, params, self.returnq))
		results = self.returnq.get()
		if results[0] == "ERROR":
			self.error = results[1]
			return

		self.rows = results[1]

def setupDB(datadir):
	DBQuery.dbQueue = Queue()
	DBQuery.dbThread = DBaccess(DBQuery.dbQueue, datadir)
		
def dbcommit():
	print "lol timered commit"
	DBQuery.dbQueue.put("COMMIT")

