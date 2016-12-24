import json
import web

import cloudserver

urls = (
	"/(.+)", "Collect")

class Collect:
    def POST(self,Id):
        raw_data=web.data()
        data=json.loads(raw_data)
        cloudserver.db.indirectSensingCollecting(Id,data['energy'])
        print(str(data))
        return "200 OK" 







IndirectSensing = web.application(urls, locals())