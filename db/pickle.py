# -*- coding: utf-8 -*-
import shelve, os

def init(x):
	""" Starts a connection with database 'x' """
	return shelve.open(x.database_name)

def close(x):
	""" Syncs and closes database connection """
	x.sync()
	x.close()

def login(x, email, password):
	""" Checks if user with said email and password is correct first element of return arg will be true if valid """
	# {"Users":{email:{UID:0, Password:"", Salt:""}, "Files":{uid:{filepath:[filepath, clonepath, hash, dateuploaded, filesize, encrypted, individual]}}}
	if email in x.keys():
		if x["Users"][email]["Password"] == password:
			return [True, ""]
		else:
			return [False, "Login Incorrect"]
	return [False, ""]

def addfile(x, uid, filepath, clonepath, fhash, dateupload, filesize, encrypted=1, individual=0):
	""" Adds a file to the db """
	if uid in x["Files"].keys() and filepath in x["Files"][uid].keys():
		return [False, "File Already Exists."]
	if not uid in x["Files"]:
		x["Files"][uid] = {filepath:[clonepath, fhash, dateuploaded, filesize, encrypted, individual]}
	else:
		x["Files"][uid][filepath] = [clonepath, fhash, dateuploaded, filesize, encrypted, individual]
	return [True, ""]

def rmfile(x, uid, filepath, fhash):
	""" Removes a file from db """
	if uid in x["Files"].keys() and filepath in x["Files"][uid].keys():
		ntemp = x[uid]
		del ntemp[filepath]
		x[uid] = ntemp
		return [True, ""]
	return [False, "Can't find file"]

def calculateused(x, uid):
	""" calculates total file size. """
	return [sum([i for i in [x["Files"][uid][n][3] for n in x["Files"][uid].keys()]]), ""]

def getsalt(x, email):
	""" Gets salt for user """
	if email in x["Users"].keys():
		return [x["Users"][email]["Salt"], ""]
	return [False, "User does not exist."]

	
