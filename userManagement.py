import web
import cloudserver
urls = ("/","userManagement")

class userManagement:
	def POST(self):
		raw_data=web.data()
		userData=raw_data.split(',')
		if (len(userData) == 0):
			return "no username provided"
		length = len(userData)
		deviceID = userData[0]
		if (len(userData) == 1):
			if (not cloudserver.db.deviceIDCheckAvailability(deviceID)):
				return "0" #already registered
			else:
				return "1" #need to register
		if (len(userData) == 2):
			if (not cloudserver.db.deviceIDCheckAvailability(deviceID)): #not available
				return "device already registered"
			if (not cloudserver.db.screenNameCheckAvailability(userData[1])): #not available
				return "screen name taken"
			cloudserver.db.screenNameRegister(userData[1], deviceID, True)
			return "0"
		if (len(userData) == 3):
			cloudserver.db.userIDRemoveAll(deviceID)
			return "0"
		if (len(userData) == 4): # device ID, username, nothing, nothing
			username = userData[1]
			if (cloudserver.db.updateName(deviceID, username)):
				return "0" #successfully changed device ID
			else:
				return "1" #screen name not found
		return "too many parameters"
		#if (len(userData) == 1):
		#	ret = cloudserver.db.userIDLookup(deviceID)
		#	if (ret is None):
		#		return "100"
		#	else:
		#		return cloudserver.db.getAttributes(ret)
		#if (userData[0] == "^^^"):
		#	if (len(userData) == 6):
		#		freq = int(float(userData[3]))
		#		if (userData[4] == "true"):
		#			wifi = True
		#		else:
		#			wifi = False
		#		if (userData[5] == "true"):
		#			public = True
		#		else:
		#			public = False
		#		user = cloudserver.db.userIDLookup(userData[2])
		#		if (cloudserver.db.rankingUpdateName(user, userData[1], freq, wifi, public)== False):
		#			return "Username Taken"
		#		if (cloudserver.db.screenNameUpdate(userData[1], userData[2])== False):
		#			return "Username Taken"
		#		return "updated"
		#	return "failed update"
		#username = userData[1]
		#if (username == "100"):
		#	return "Special Name"
		#cloudserver.db.userIDRemoveAll(deviceID)
		#if (cloudserver.db.screenNameCheckAvailability(username)):
		#	if (cloudserver.db.screenNameRegister(username, deviceID, True)):
		#		if (len(userData) == 5):
		#			cloudserver.db.registerForRankingInfo(username, userData[2], userData[3], userData[4])
		#		else:
		#			cloudserver.db.registerForRanking(username)
		#		return "0" #success
		#	else:
		#		return "Duplicate Username" #duplicate username
		#else:
		#	return "Username Taken" #username taken
		#return "case 3"


	def GET(self):
		user_data = web.input(id=None)
		if user_data.id == None:
			return "Error: please provide valid user ID."
		if (cloudserver.db.getControl(user_data.id) == True):
			return "true"
		else:
			return "false"
		return "true"


userMGM = web.application(urls, locals());

