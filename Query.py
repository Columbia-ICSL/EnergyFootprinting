import json
import web
import calendar
import datetime

import cloudserver
urls = (
    "/QueryRoom/(.+?)","QueryRoom", #room ID + time range
    "/QueryPerson/(.+?)","QueryPerson" #person ID +

)

class QueryRoom:
    def POST(self,postion):
        data = web.data()
        pass
        return "success"
    def GET(self,room):
        if room=="":
            return "no room to query"
        raw_time=web.input()
        
        
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=raw_time['end']
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=raw_time['start']
            
        
        return db.QueryRoom(room,start,end)

class QueryPerson:
    def all(self,person):
        if person=="":
            return "no name []"
        print person
        result = cloudserver.db.QueryPerson(person,0,2**10)
       # return """[{"type":"Plug","unit":"watts","value":15,"description":"plugmeter"},{"type":"HVAC","value":10,"unit":"watts","description":"Approximation from Pressure&Temperature"}]"""
        return result
        #"person name: {0}".format(person)
    def POST(self,person):
        return self.all(person)
    def GET(self,person):
        return self.all(person)
#
#
query = web.application(urls, locals())


