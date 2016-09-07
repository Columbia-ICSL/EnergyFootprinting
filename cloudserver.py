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
import LocationBeacons
import locationTraining
import userRanking
import suggestionDecisions
import userManagement
import Query
import Manage
from bson import ObjectId
from threading import Thread
import suggestionsEngine
from trainingData import training

urls = (
 
    "/api/EnergyReport",Energy.EnergyReport,
    "/api/LocationReport",Location.LocationReport, #room ID, +(timestamp)?
    "/api/LocationReportAlt",Location.LocationReportAlt, #room ID, +(timestamp)?
    "/api/Query",Query.query, #room ID + time range
#    "/api/Beacons", "beacons",
    "/api/Beacons", LocationBeacons.Beacons,
    "/api/userRankings", userRanking.userRankings,
    "/api/locationTraining", locationTraining.locationTraining,
    "/api/userManagement", userManagement.userMGM,
    "/api/suggestionDecisions", suggestionDecisions.Decisions,
    "/frontend/(.+)", "frontend",
    "/api/SaveShot",Manage.Manager,
    "/realtime/(.*)","Realtime",
    "/realtime","Realtime",
    "/debug","Debug",
    "/recent","Recent",
    "/","index"
)

from DBMgr import MongoJsonEncoder

               
#trainingData = training.datapoints
#trainingLabels = training.labelNumber
#outfile = "backup2.txt"
#with open(outfile, 'w') as file:
#    file.writelines('\t'.join(str(j) for j in i) + '\n' for i in trainingData)
#outfile2 = "backuplabels2.txt"
#with open(outfile2, 'w') as file:
#    file.writelines(str(rooms[i]) + '\n' for i in trainingLabels)

#client = pymongo.MongoClient()
#client = pymongo.MongoClient('localhost', 27017)
#db = client.test_database
db=DBMgr.DBMgr()
SE = suggestionsEngine.suggestionsEngine()
#TD = generateTrainingData()

render = web.template.render('templates/')

class Debug:
    def GET(self):
        return DBMgr.dump_debug_log()
class Recent:
    def GET(self):
        return DBMgr.dump_recent_raw_submission()
class Realtime:
    def GET(self,person=None):
        if "full" in web.input():
            return db.ShowRealtime(concise=False)
        if "personal" in web.input():
            return db.ShowRealtimePersonalSummary()
        return db.ShowRealtime(person)

class index:
    def GET(self):

        return web.seeother('/static/')



        #return "Hello {0}".format(name)
class frontend:
    def GET(self,person):
        print(person)
        t = time.time() 
        result = db.QueryPerson(person,t-86400*7+1,t)
        #data=json.dumps(result)
        data=MongoJsonEncoder().encode(result) 
        return render.chart(data)
class room:
    def GET(self,room):
        input=str(web.input())
        print(input)
        print(room)

        #return input+" {0}".format(name)
        return db.QueryRoom(room,0,2**32)

#class beacons: 
#    def POST(self):
#        raw_data = web.data()
#        db.SaveLocationData(0,12)
#        return str(raw_data)
#    def GET(self):
#        result = db.QueryLocationData(0)
#        return result



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
