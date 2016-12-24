import json
import web
import calendar
import datetime

import cloudserver
urls = (
	"/BuildingFootprint/", "BuildingFootprint",
	"/BuildingFootprintDisaggregated/", "BuildingFootprintDisaggregated")

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


dataExtraction = web.application(urls, locals())