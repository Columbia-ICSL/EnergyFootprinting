import web
import cloudserver

urls = ("/", "appSupport",
"/localization/", "userLocalizationAPI", "/userNames/", "userNames")

class userNames:
        def GET(self):
                return cloudserver.db.getAllUsers()

class appSupport:
	def GET(self):
		data = web.input(id=None)
		if cloudserver.db.userIDLookup(data.id) == None :
			return "Invalid userID"
		else:
			if cloudserver.db.getControl(data.id):
				ret={
					"value":0,
					"HVAC":0,
					"Light":0,
					"Electrical":0
				}
				return cloudserver.db._encode(ret, False)
			location = cloudserver.db.getUserLocation(data.id)
			ret = cloudserver.db.calculateEnergyFootprint(location)
			return ret
		return "How did you get here"

class userLocalizationAPI:
	def GET(self):
		return cloudserver.db.getUserLocalizationAPI()
appURL = web.application(urls, locals());
