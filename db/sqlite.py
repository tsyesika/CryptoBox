# -*- coding: utf-8 -*-
import sqlite3, os

def init(x):
	""" Starts a connection with database 'x' """
	installed = False
	if os.path.isfile(x.database_name):
		installed = True
	try:
		conn = sqlite3.connect(x.database_name)
	except:
		return [None, "Cannot connect to the database. ('%s')" % x.database_location]
	curs = conn.cursor()
	if not installed:
		install((curs, conn))
	return [(curs, conn), ""]

def install(x):
	""" Creates Users and Files Table """
	x[0].execute("""CREATE TABLE Users(
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		Email VARCHAR(256),
		Password CHAR(64),
		Salt CHAR(16),
		Size INT,
		PromotionalID INT,
		DateRegistered CHAR(10)
	)""")
	
	x[0].execute("""
	CREATE TABLE Files(
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		UID INT,
		FilePath VCHAR(255),
		ClonePath VCHAR(255),
		FHash VCHAR(16),
		DateUploaded CHAR(10),
		FileSize REAL,
		Encrypted INT,
		Individual INT
	);""")
	
	x[1].commit()
	
	# Although some file systems like resierfs and also ntfs (in combo with windows) allow greater than 255
	# the sql limit is usually 255 for vchar so I've used that as a fixed limit.
	
	# NB: Encrypted & Individual only hold 0 or 1 so bool (does it exist? or TINYINT?) - both need more research if sqlite supports..

def close(x):
	""" Commits and closes database connection (give connection tuple as x) """
	x[1].commit()
	x[0].close()
	return [True, ""]

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid."""
	x[0].execute("SELECT * FROM Users WHERE Email=? AND Password=?", (email, password))
	if x[0].fetchall() == []:
		return [False, "Login Incorrect"]
	return [True, ""]

def addfile(x, uid, filepath, clonepath, fhash, dateupload, filesize, encrypted=1, individual=0):
	""" Adds a file to db """
	x[0].execute("SELECT * FROM Files WHERE UID=? AND FilePath=? AND FHash=?", (uid, filepath, fhash))
	if x[0].fetchall() == []:
		x[0].execute("INSERT INTO Files(UID, FilePath, ClonePath, FHash, DateUploaded, FileSize, Encrypted, Individual) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (uid, filepath, clonepath, fhash, dateupload, filesize, encrypted, individual))
	else:
		return [False, "File Already Exists."]
	return [True, ""]
	
def rmfile(x, uid, filepath):
	""" Removes a file from db """
	x[0].execute("SELECT * From Files WHERE UID=? AND FilePath=?", (uid, filepath))
	if x[0].fetchall() == []:
		return [False, "Can't find file"]
	x[0].execute("DELETE FROM Files WHERE UID=? AND FilePath=?", (uid, filepath))
	return [True, ""]

def calculateused(x, uid):
	""" calculates total file size. """
	x[0].execute("SELECT filesize FROM Files WHERE UID=?", (uid,))
	return [sum([x1[0] for x1 in x[0].fetchall()]), ""]
	
def getsalt(x, email):
	""" Gets salt for user """
	x[0].execute("SELECT Salt FROM Users WHERE Email=?", (email,))
	res = x[0].fetchall()
	if res:
		return [res[0][0], ""]
	return [False, "Couldn't find user."]
	
