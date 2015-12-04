import web
import json
import os
import datetime
import time
import calendar
import pymongo

import blog
import DBMgr
import Energy
import Location
import Query
import Manage
from bson import ObjectId

urls = (
 
    "/api/EnergyReport",Energy.EnergyReport,
    "/api/LocationReport",Location.LocationReport, #room ID, +(timestamp)?
    "/api/Query",Query.query, #room ID + time range
    "/frontend/(.+)", "frontend",
    "/api/SaveShot",Manage.Manager,
    "/api/Realtime/(.*)",Realtime,
    "/debug","Debug",
    "/recent","Recent",
    "/","index"
)

from DBMgr import MongoJsonEncoder



#client = pymongo.MongoClient()
#client = pymongo.MongoClient('localhost', 27017)
#db = client.test_database
db=DBMgr.DBMgr()


render = web.template.render('templates/')

class Debug:
    def GET(self):
        return DBMgr.dump_debug_log()
class Recent:
    def GET(self):
        return DBMgr.dump_recent_raw_submission()
class Realtime:
    def GET(self,person):
        return DBMgr.ShowRealtime(person)

class index:
    def GET(self):

        return web.seeother('/static/')



        #return "Hello {0}".format(name)
class frontend:
    def GET(self,person):
        print person
        t = time.time() 
        result = db.QueryPerson(person,t-86400*7+1,t)
        #data=json.dumps(result)
        data=MongoJsonEncoder().encode(result) 
        return render.chart(data)
class room:
    def GET(self,room):
        input=str(web.input())
        print input
        print room

        #return input+" {0}".format(name)
        return db.QueryRoom(room,0,2**32)




class MyApplication(web.application):
    def run(self, port=8080, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))
def notfound():
    return web.notfound("404 Not Found")

    # You can use template result like below, either is ok:
    #return web.notfound(render.notfound())
    #return web.notfound(str(render.notfound()))
def run():
    app = MyApplication(urls, globals())
    app.notfound = notfound
    app.run(port=8000)
