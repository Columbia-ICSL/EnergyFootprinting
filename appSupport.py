import web
import cloudserver

urls = ("/", "appSupport")

class appSupport:
	def GET(self):
		data = web.input(id=None)
		if cloudserver.db.userIDLookup(data.id) == None :
			return "Invalid userID"
		else:
			location = cloudserver.db.getUserLocation(data.id)
		return location

appURL = web.application(urls, locals());
