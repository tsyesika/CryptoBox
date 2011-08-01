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
		[False, "Couldn't connect with database"]
	
	return [con, ""]
	
def close(x):
	""" Commits and closes database connection """
	x[0].commit()
	x[0].close()
	return [True, ""]

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid."""
	x[0].query("SELECT * FROM Users WHERE Email='?' AND Password='?'", (email, password))
	res = x[0].store_result()
	if not res:
		return [False, "Login Incorrect"]
	if x[0].fetch_row() == ():
		return [False, "Login Incorrect"]
	return [True, ""]
	
