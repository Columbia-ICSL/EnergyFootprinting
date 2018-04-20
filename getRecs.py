import web
import cloudserver

urls = ("/", "getRecs")
#"/localization/", "userLocalizationAPI", 
#"/userNames/", "userNames",
#"/buildingFootprint/", "buildingFootprint",
#"/multipleUsers/", "multipleUsers")

class getRecs:
	def GET(self):
		data = web.input(id=None)
		if cloudserver.db.userIDLookup(data.id) == None :
			return cloudserver.db._encode({"recs":-1}, False)
		else:
			testValue = cloudserver.db.recommendationsAPI()
			return cloudserver.db._encode({"recs":testValue}, False)
		return "How did you get here"


appURL = web.application(urls, locals());