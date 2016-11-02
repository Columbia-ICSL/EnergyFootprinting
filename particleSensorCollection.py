import json
import web
import cloudserver

urls = (
	"/(.+)", "CollectParticles")

class CollectParticles:
	def POST(self, Id):
		raw_data=web.data()
		data=json.loads(raw_data)
		cloudserver.db.particleSensorCollecting(Id, data['sensorNumber'], data['PM1L'], data['PM25L'], data['PM10L'],
			data['PM1A'], data['PM25A'], data['PM10A'], data['um03'], data['um05'], data['um1'], data['um25'], data['um50'], data['um10'])

	    print(str(data))
        return "200 OK" 

particleSensing = web.application(urls, locals())