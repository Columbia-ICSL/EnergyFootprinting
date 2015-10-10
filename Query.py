
import web
import json
urls = (
    "/QueryRoom/(.*)","QueryRoom", #room ID + time range
    "/QueryPerson/(.*)","QueryPerson" #person ID +

)

class QueryRoom:
    def POST(self,postion):
        data = web.data()
        pass
        return "success"
    def GET(self,position):
        return "position is: " +position
class QueryPerson:
    def GET(self,person):
        return "person name: {0}".format(person)
#
#
query = web.application(urls, locals())

urls2=(
"/bb","bb"
)
class bb:
    def GET(self):
        return "test sucess "
test=web.application(urls2,locals())
