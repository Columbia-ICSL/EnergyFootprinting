import json
import web

import cloudserver


urls = (
	"/SaveBACNET","SaveBACNET",
	"/SaveParameters", "SaveParameters"
)


class SaveBACNET:
    def POST(self):
    	print("Reporting BACNET")
        raw_data=web.data()
        data=json.loads(raw_data)
        for device in data:
            cloudserver.db.ReportEnergyValue(device, data[device], None)
        return "200 OK"

class SaveParameters:
	def POST(self):

		print("Reporting Parameters")
		raw_data=web.data()
		data=json.loads(raw_data)
		cloudserver.db.SaveParameters(data)


EnergyReportBACNET = web.application(urls, locals())