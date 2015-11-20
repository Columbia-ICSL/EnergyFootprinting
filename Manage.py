import json
import web

import cloudserver


urls = (
"/","SaveShot"
)

class SaveShot:
    def POST(self):
        pass
        return "post"
    def GET(self):
        cloudserver.db.SaveShot()
        print "SaveShot!"
        pass
        return "get"
Manager = web.application(urls, locals())
