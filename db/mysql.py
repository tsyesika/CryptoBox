import _mysql

def init(x):
	""" Starts a connection with database 'x' """
	try:
		con = _mysql.connect(host=x.database_host,
						 user=x.database_username,
						 passwd=x.database_password,
						 db=x.database_name,
						 port=x.database_port)
	
	except:
		return [None, "Cannot connect to the database. ('%s')" % x.database_host]
	
	return [con, ""]
	
def close(x):
	""" Commits and closes database connection """
	x[0].commit()
	x[0].close()
	return [True, ""]

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid."""
	x[0].query("SELECT * FROM Users WHERE Email='%s' AND Password='%s'" % (x[0].escape_string(email), x[0].escape_string(password)))
	res = x[0].store_result()
	if not res:
		return [False, "Login Incorrect"]
	if res.fetch_row() == ():
		return [False, "Login Incorrect"]
	return [True, ""]

def addfile(x, uid, filepath, clonepath, fhash, dateupload, filesize, encrypted=1, individual=0):
	""" Adds a file to db """
	x[0].query("SELECT * From Files WHERE UID=%s AND FilePath='%s' AND FHash='%s'" % (x[0].escape_string(str(uid)), x[0].escape_string(filepath), x[0].escape_string(fhash)))
	res = x[0].store_result()
	if not res or res.fetch_row() == ():
		x[0].query("INSERT INTO Files(UID, FilePath, ClonePath, FHash, DateUploaded, FileSize, Encrypted, Individual) VALUES(%s, '%s', '%s', '%s', '%s', %s, %s, %s)", (
		x[0].escape_string(str(uid)),
		x[0].escape_string(filepath),
		x[0].escape_string(clonepath), 
		x[0].escape_string(fhash), 
		x[0].escape_string(dateuploaded), 
		x[0].escape_string(str(filesize)),
		x[0].escape_string(str(encrypted),
		x[0].escape_string(str(individual))))
	else:
		return [False, "File Already Exists."]
	return [True, ""]

def rmfile(x, uid, filepath, fhash):
	""" Removes a file from db """
	x[0].query("SELECT * From Files WHERE UID=%s AND FilePath='%s' AND FHash='%s'" % (x[0].escape_string(str(uid)), x[0].escape_string(filepath), x[0].escape_string(fhash)))
	res = x[0].store_result()
	if res and res.fetch_row() != ():
		x[0].query("DELETE FROM Files WHERE UID=%s AND FilePath='%s' AND FHash='%s'" % (x[0].escape_string(str(uid)), x[0].escape_string(filepath), x[0].escape_string(fhash)))
	else:
		return [False, "Can't find file"]
	return [True, ""]

def calculateused(x, uid):
	""" calculates total file size. """
	x[0].query("SELECT filesize FROM Files WHERE UID=%s" %s x[0].escape_string(str(uid)))
	res = x[0].store_result()
	return [sum([x1[0] for x1 in x[0].fetchall()]), ""]

def getsalt(x, email):
	""" Gets salt for user """
	x[0].query("SELECT Salt FROM Users WHERE Email='%s'" % x[0].escape_string(email))
	if not res:
		return [False, "Couldn't find user."]	
	res = x[0].store_result()
	if not res:
		return [False, "Couldn't find user."]
	return [res[0][0], ""]
	
	
		
		
