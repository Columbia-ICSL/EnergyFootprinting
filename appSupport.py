import web
import cloudserver

urls = ("/", "appSupport")

class appSupport:
	def GET(self):
		data = web.input(id=None)
		if cloudserver.db.userIDLookup(data.id) == None :
			return "Invalid userID"
		else:
			print "user found"
			location = cloudserver.db.getUserLocation(data.id)
			print location
			ret = cloudserver.db.calculateRoomFootprint(location)
		return ret["value"]

appURL = web.application(urls, locals());
