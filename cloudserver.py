import web
import json
import os
import datetime
import pymongo
import blog
import DBMgr

urls = (
    "/api/EnergyReport/(.+)/SavePlug","SavePlug", #raw values: watts, kwh
    "/api/EnergyReport/(.+)/SaveHVAC","SaveHVAC",  #raw values: pressure+temp
    "/api/EnergyReport/(.+)/SaveLight","SaveLight", #raw values: on or off / watts
    "/api/LocationReport/(.+)","SavePosition", #room ID, +(timestamp)?
    "/api/QueryRoom/(.*)","QueryRoom", #room ID + time range
    "/api/QueryPerson/(.*)","QueryPerson", #person ID +
    "/blog",blog.app_blog,

    "/(.+)/index","index"

)




#client = pymongo.MongoClient()
#client = pymongo.MongoClient('localhost', 27017)
#db = client.test_database
db=DBMgr.DBMgr()




class index:
    def GET(self, path):
	    if path=="":
		    return "Hello world from bitbucket! this is the icsl energy foot-print api; try out /api/query/room/* "

        return path
    def POST(self,query):
        return str(query)

        #return "Hello {0}".format(name)
class room:
    def GET(self,room):
        input=str(web.input())
        print input
        print room

        #return input+" {0}".format(name)
        return db.QueryRoom(room,0,2**32)


class SaveHVAC:
    def POST(self):
        pass
        return 0
class SaveLight:
    def POST(self):
        pass
        return 0


class SavePlug:
    def POST(self):
        raw_data = web.data() # you can get data use this method
        data=json.loads(raw_data)
        room=data["room"]
        description=data["name"]
        energy=data["energy"]
        power=data["power"]
        db.SavePlug(room,description,energy,power)

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
