# -*- coding: utf-8 -*-
import shelve, os

def init(x):
	""" Starts a connection with database 'x' """
	return [shelve.open(x.database_name), ""]

def close(x):
	""" Syncs and closes database connection """
	x.sync()
	x.close()

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid """
	# {"Users":{email:{UID:0, Password:"", Salt:""}, "Files":{uid:{filepath:[filepath, clonepath, hash, dateuploaded, filesize, encrypted, individual]}}}
	if email in x[0].keys():
		if x["Users"][email]["Password"] == password:
			return [True, ""]
		else:
			return [False, "Login Incorrect"]
	return [False, ""]

def addfile(x, uid, filepath, clonepath, fhash, dateupload, filesize, encrypted=1, individual=0):
	""" Adds a file to the db """
	if uid in x[0]["Files"].keys() and filepath in x[0]["Files"][uid].keys():
		return [False, "File Already Exists."]
	if not uid in x["Files"]:
		x[0]["Files"][uid] = {filepath:[clonepath, fhash, dateuploaded, filesize, encrypted, individual]}
	else:
		x[0]["Files"][uid][filepath] = [clonepath, fhash, dateuploaded, filesize, encrypted, individual]
	return [True, ""]

def rmfile(x, uid, filepath, fhash):
	""" Removes a file from db """
	if uid in x[0]["Files"].keys() and filepath in x[0]["Files"][uid].keys():
		ntemp = x[uid]
		del ntemp[filepath]
		x[uid] = ntemp
		return [True, ""]
	return [False, "Can't find file"]

def calculateused(x, uid):
	""" calculates total file size. """
	return [sum([i for i in [x[0]["Files"][uid][n][3] for n in x[0]["Files"][uid].keys()]]), ""]

def getsalt(x, email):
	""" Gets salt for user """
	if email in x[0]["Users"].keys():
		return [x["Users"][email]["Salt"], ""]
	return [False, "User does not exist."]

	
