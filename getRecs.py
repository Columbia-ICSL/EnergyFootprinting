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
		if cloudserver.db.userIDLookup(data.id) == None:
			json_return={
            	"location":"Out of Lab",
            	"location_id":"Out of Lab",
            	"balance":0,
            	"tempBalance": 0,
            	"suggestions":[]
       		}
			return cloudserver.db._encode(json_return)
		else:
			ret = cloudserver.db.returnRecs(data.id)
			return ret
			#cloudserver.db._encode({"recs":testValue}, False)
		return "How did you get here"


appURL = web.application(urls, locals());