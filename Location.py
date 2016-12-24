
import web
import json
import cloudserver
urls = (
"/(.+)","SavePosition" #room ID, +(timestamp)?

)

class SavePosition:
    def POST(self,personID):
        raw_data = web.data() # you can get data use this method
        data=json.loads(raw_data)
        room=data["room"]
        #confidence=data["confidence"]
        #timestamp, since, deviceID...
        return str(cloudserver.db.ReportLocationAssociation(personID,room,raw_data))
    def GET(self,personID):
        return "Location Reportint endpoint:"+personID #str(cloudserver.db.CheckLocation(personID))

LocationReport = web.application(urls, locals())

urls_alt = (
	"/(.+)","LocationReportHTTPQuery"
)
class LocationReportHTTPQuery:
	def GET(self,personID):
		user_data = web.input()
		room=user_data["room"]
		raw={}
		if "confidence" in user_data:
			raw["confidence"]=confidence
		raw["_http"]=web.data()
		return str(cloudserver.db.ReportLocationAssociation(personID,room,raw_data))


LocationReportAlt = web.application(urls_alt, locals())
