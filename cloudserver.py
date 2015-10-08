import web
import json
import os
import datetime
import pymongo
import blog
import DBMgr

urls = (
    "/api/EnergyReport/(.+)/Plug","SaveEnergy", #raw values: watts, kwh
    "/api/EnergyReport/(.+)/HVAC","SaveHVAC",  #raw values: pressure+temp
    "/api/EnergyReport/(.+)/Light","SaveLight", #raw values: on or off / watts
    "/api/LocationReport/(.+)","SavePosition", #room ID, +(timestamp)?
    "/api/QueryRoom/(.*)","QueryRoom", #room ID + time range
    "/api/QueryPerson/(.*)","QueryPerson", #person ID + 
    "/blog",blog.app_blog,

    "/(.*)","index"

)




#client = pymongo.MongoClient()
#client = pymongo.MongoClient('localhost', 27017)
#db = client.test_database
db=DBMgr.DBMgr()

class h:
    def GET(self):
        return "test haha"



class index:
    def GET(self, path):
	if path=="":
		return "Hello world from bitbucket! this is the icsl energy foot-print api; try out /api/query/room/* "

        return path

        #return "Hello {0}".format(name)
class room:
    def GET(self,room):
        input=str(web.input())
        print input
        print room

        #return input+" {0}".format(name)
        return db.QueryRoomRealtime(room)



class SaveEnergy:
    def POST(self):
        raw_data = web.data() # you can get data use this method
        data=json.loads(raw_data)
        room=data["room"]
        description=data["name"]
        energy=data["energy"]
        power=data["power"]
        db.SaveEnergyPower(room,description,energy,power)

        return "200 OK"
class SavePosition:
    def POST(self):
        data = web.data()
        pass
        return 0
class MyApplication(web.application):
    def run(self, port=8080, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))
def run():
    app = MyApplication(urls, globals())
    app.run(port=8000)
