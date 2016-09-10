import web
import cloudserver
urls = ("/","userManagement")

class userManagement:

	def POST(self):
		raw_data=web.data()
		userData=raw_data.split(',')
		if (len(userData) == 0):
			return "case 1"
		deviceID = userData[0]
		if (len(userData) == 1):
			ret = cloudserver.db.userIDLookup(deviceID)
			if (ret is None):
				return "100"
			else:
				return cloudserver.db.getAttributes(ret)
		if (userData[0] == "^^^"):
			if (len(userData) == 6):
				freq = int(float(userData[3]))
				if (userData[4] == "true"):
					wifi = True
				else:
					wifi = False
				if (userData[5] == "true"):
					public = True
				else:
					public = False
				user = cloudserver.db.userIDLookup(userData[2])
				if (!cloudserver.db.rankingUpdateName(user, userData[1], freq, wifi, public)):
					return "Username Taken"
				if (!cloudserver.db.screenNameUpdate(userData[1], userData[2])):
					return "Username Taken"
				
				return "updated"
			return "failed update"
		username = userData[1]
		if (username == "100"):
			return "Special Name"
		cloudserver.db.userIDRemoveAll(deviceID)
		if (cloudserver.db.screenNameCheckAvailability(username)):
			if (cloudserver.db.screenNameRegister(username, deviceID, True)):
				if (len(userData) == 5):
					cloudserver.db.registerForRankingInfo(username, userData[2], userData[3], userData[4])
				else:
					cloudserver.db.registerForRanking(username)
				return "0" #success
			else:
				return "Duplicate Username" #duplicate username
		else:
			return "Username Taken" #username taken
		return "case 3"


	def GET(self):
		user_data = web.input(id="no data")
        if (cloudserver.db.getControl(user_data.id) == True):
        	return "true"
        else:
        	return "false"


userMGM = web.application(urls, locals());

