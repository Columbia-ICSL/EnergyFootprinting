import json
import web
import calendar
import datetime

import cloudserver
urls = (
	"/BuildingFootprint/", "BuildingFootprint",
	"/BuildingFootprintDisaggregated/", "BuildingFootprintDisaggregated",
	"/PersonalConsumption/", "PersonalConsumption")

class BuildingFootprint:
	def GET(self):
		raw_time = web.input()
		if "end" not in raw_time:
			end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		else:
			end = float(raw_time['end'])
		if "start" not in raw_time:
			start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60 #1 day
		else:
			start = float(raw_time['start'])
		return cloudserver.db.buildingFootprint(start, end)

class BuildingFootprintDisaggregated:
	def GET(self):
		raw_time = web.input()
		if "end" not in raw_time:
			end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		else:
			end = float(raw_time['end'])
		if "start" not in raw_time:
			start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60 #1 day
		else:
			start = float(raw_time['start'])
		return cloudserver.db.buildingFootprintDisaggregated(start, end)

class PersonalConsumption:
	def GET(self):
		print("Got to Personal Consumption")
		raw_data = web.input()
		end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		if "end" in raw_data:
			end = float(raw_data['end'])

		start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60 #1 day
		if "start" in raw_data:
			start = float(raw_data['start'])

		user = "Peter Wei"
		if "user" in raw_data:
			user = raw_data['user']

		return cloudserver.db.personalFootprint(user, start, end)



dataExtraction = web.application(urls, locals())







