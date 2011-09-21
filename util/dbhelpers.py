#db helpers, didn't put this in db.py just because.
from db import DBQuery

def checkcreatetable(name, createstmt):
	query = ('''SELECT name FROM sqlite_master WHERE name=?;''', (name,))
	if query.error:
		#uh oh....
		print "What happened?: %s" % query.error
		return False

	if not query.rows:
		query.query(createstmt)
		# should probably make sure this returns valid
		if query.error:
			print "Error creating table... %s" % query.error
			return False
	return True
