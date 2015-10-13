
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
        confidence=data["confidence"]
        #timestamp, since, deviceID...
        return str(cloudserver.db.SaveLocation(personID,room,confidence))
    def GET(self,personID):
        return str(cloudserver.db.CheckLocation(personID))

LocationReport = web.application(urls, locals())
