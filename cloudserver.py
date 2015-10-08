import web
import json
import os
import datetime
import pymongo
import blog
import DBMgr

urls = (
    "/api/smartthings/SaveEnergy","SaveEnergy",
    "/api/smartthings/SavePeople","SavePosition",
    "/api/query/room/(.*)","room",
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
		return "Hello world!"

        return path

        #return "Hello {0}".format(name)
class room:
    def GET(self,room):
        input=str(web.input())
        print input
        print room

        #return input+" {0}".format(name)
        return db.QueryRealtime(room)



class SaveEnergy:
    def POST(self):
        raw_data = web.data() # you can get data use this method
        data=json.loads(raw_data)
        room=data["room"]
        description=data["name"]
        energy=data["energy"]
        db.SaveEnergy(room,description,energy)

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
