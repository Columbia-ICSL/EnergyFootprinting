import json
import web

import cloudserver


urls = (
"/(.+)","Manage"
)

class Manage:
    def POST(self,Id):
        pass
        return "post"
    def GET(self):
        cloudserver.db.SaveShot()
        print "SaveShot!"
        pass
        return "get"
Manager = web.application(urls, locals())
