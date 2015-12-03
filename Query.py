import json
import web
import calendar
import datetime

import cloudserver
urls = (
    "/QueryRoom/(.+?)","QueryRoom", #room ID + time range
    "/QueryPerson/(.+?)","QueryPerson", #person ID +
    "/QueryPersonMulti/(.+)","QueryPersonMulti", #person ID +
    "/QueryEvents/(.*)","QueryEvents", #person ID +

)

class QueryRoom:
    def POST(self,postion):
        return
    def GET(self,room):
        if room=="":
            return "no room to query"
        raw_time=web.input()
        
        
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=float(raw_time['end'])
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=float(raw_time['start'])
        return cloudserver.db.QueryRoom(room,start,end)

class QueryPerson:

    def POST(self,person):
        return
    def GET(self,person):
        if person=="":
            return web.notfound("Error: no person name provided")
        raw_time=web.input()
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=float(raw_time['end'])
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=float(raw_time['start'])
            
        
        return cloudserver.db.QueryPerson(person,start,end)

class QueryPersonMulti:

    def POST(self,personList):
        return
    def GET(self,personList):
        if personList=="":
            return web.notfound("Error: no persons list provided")
        raw_time=web.input()
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=float(raw_time['end'])
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=float(raw_time['start'])
        
        people=personList.split(",")
        print people
        return cloudserver.db.QueryPersonMulti(people,start,end)


class QueryEvents:

    def POST(self,person):
        return
    def GET(self,person):
        raw_time=web.input()
        if "end" not in raw_time:
            end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        else:
            end=float(raw_time['end'])
        if "start" not in raw_time:
            start=calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
        else:
            start=float(raw_time['start'])
        if person=="":
            return cloudserver.db.QueryAllEvents(start,end)
        return cloudserver.db.QueryEvents(person,start,end)
#
#
query = web.application(urls, locals())


