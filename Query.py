import json
import web
import cloudserver
urls = (
    "/QueryRoom/(.?)","QueryRoom", #room ID + time range
    "/QueryPerson/(.*)","QueryPerson" #person ID +

)

class QueryRoom:
    def POST(self,postion):
        data = web.data()
        pass
        return "success"
    def GET(self,room):
        print room
        return room
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


