import json
import web
import cloudserver

urls = (
"/","BeaconVals")

class BeaconVals:
    def POST(self, vals):
        raw_data=web.data()
        data = json.loads(raw_data)
        
        return "Hello World!"
    def GET(self):
        return "Hello, world"

Beacons = web.application(urls, locals());
