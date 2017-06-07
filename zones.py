import json
import web
import cloudserver

urls = ("/", "zones",
		"/test", "testing")

class zones:
	def POST(self):
		raw_data=web.data()
		locs = raw_data.split(',')
		x = locs[0]
		y = locs[1]
		beaconData = locs[2:]
		cloudsever.db.insertLocationTrainingData(x, y, beaconData)
		return

class testing:
	def POST(self):
		raw_data=web.data()
		locs = raw_data.split(',')
		assert(locs[0] == "beacons")
		beaconData = locs[1:]
		cloudsever.db.insertLocationTrainingData(beaconData)
		return


zonesTraining = web.application(urls, locals());