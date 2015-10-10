
import web
import json
import cloudserver
urls = (
"/(.+)","SavePosition" #room ID, +(timestamp)?

)

class SavePosition:
    def POST(self,postion):
        data = web.data()
        pass
        return "success"
    def GET(self,position):
        return position

LocationReport = web.application(urls, locals())
