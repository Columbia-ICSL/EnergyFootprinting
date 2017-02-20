import json
import web

import cloudserver


urls = (
	"/SaveBACNET","SaveBACNET"
)


class SaveBACNET:
    def POST(self):
    	print("Reporting BACNET")
        raw_data=web.data()
        data=json.loads(raw_data)
        for device in data:
            cloudserver.db.ReportEnergyValue(device, data[device], None)
        return "200 OK"

EnergyReportBACNET = web.application(urls, locals())