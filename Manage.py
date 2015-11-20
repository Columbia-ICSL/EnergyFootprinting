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
        pass
        return "get"
Manager = web.application(urls, locals())
