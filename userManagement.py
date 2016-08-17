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
				return ret
		username = userData[1]
		if (username == "100"):
			return "1"
		if (cloudserver.db.screenNameCheckAvailability(username)):
			if (cloudserver.db.screenNameRegister(username, deviceID)):
				return "0" #success
			else:
				return "1" #duplicate username
		else:
			return "1" #username taken
		return "case 3"

userMGM = web.application(urls, locals());