import json
import web

import cloudserver


urls = (
	"/ReportData","ReportData"
)


class ReportData:
    def POST(self):
    	print("Reporting data 203")
        raw_data=web.data()
        data=json.loads(raw_data)
        cloudserver.db.ReportOSData(data)
        return "203 OK"


reportData = web.application(urls, locals())