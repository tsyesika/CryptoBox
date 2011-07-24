import sqlite3

def init(x):
	"""Starts a connection with database 'x'"""
	try:
		conn = sqlite3.connect(x.database_location)
	except:
		return [None, "Cannot connect to the database. ('%s')" % x.database_location]
	curs = conn.cursor()
	return [(conn, curs), ""]

def close(x):
	"""Commits and closes database connection (give connection tuple as x)"""
	x[0].commit()
	x[1].close()
	return [True, ""]

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid."""
	x[0].execute("SELECT * FROM Users WHERE Email='?' AND Password='?'", (username, password))
	if x[0].fetchall() == []
		return [False, "Login Incorrect"]
	return [True, ""]

def addfile(x, uid, filepath, clonepath, fhash, dateupload, filesize, encrypted=1, individual=0):
	""" Adds a file to db """
	x[0].execute("SELECT * FROM Files WHERE UID=? AND FilePath='?' AND Hash='?'", (uid, filepath, fhash))
	if x[0].fetchall() == []:
		x[0].execute("INSERT INTO Files(UID, filepath, clonepath, fhash, dateuploaded, filesize, encrypted, individual) VALUES(?, '?', '?', '?', '?', ?, ?)", (uid, filepath, clonepath, fhash, dateuploaded, filesize, encrypted))
	else:
		return [False, "File Already Exists."]
	return [True, ""]
	
def rmfile(x, uid, filepath, fhash):
	""" Removes a file from db """
	x[0].execute("SELECT * From Files WHERE UID=? AND FilePath='?' AND Hash='?'", (uid, filepath, fhash))
	if x[0].fetchall() == []:
		return [False, "Can't find file"]
	x[0].execute("DELETE FROM Files WHERE UID=? AND FilePath='?' AND Hash='?'", (uid, filepath, fhash))
	return [True, ""]

def calculateused(x, uid):
	""" calculates total file size. """
	x[0].execute("SELECT filesize FROM Files WHERE UID=?", (uid,))
	return [sum([x1[0] for x1 in ix[0].fetchall()]), ""]
	