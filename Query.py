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
            end=int(raw_time['end'])
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=int(raw_time['start'])
            
        
        return cloudserver.db.QueryRoom(room,start,end)

class QueryPerson:

    def POST(self,person):
        return self.all(person)
    def GET(self,person):
        if person=="":
            return "no name []"
        raw_time=web.input()
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=raw_time['end']
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=raw_time['start']
            
        
        return cloudserver.db.QueryPerson(person,start,end)

#
#
query = web.application(urls, locals())


