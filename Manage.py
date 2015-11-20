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
        
        print "SaveShot!"
        
        return cloudserver.db.SaveShot()
Manager = web.application(urls, locals())
