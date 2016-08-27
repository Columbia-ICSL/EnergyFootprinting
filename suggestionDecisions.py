import json
import web
import cloudserver

urls = (
"/","DecisionVals")

class DecisionVals:
	def POST(self):
		raw_data=web.data()
		data = raw_data.split(',')
		deviceID = data[0]
		user = cloudserver.db.userIDLookup(deviceID)
		suggestion = data[1]
		coins = data[2]
		cloudserver.db.updateUserBalance(user, coins)
		return "success"

	def GET(self):
		return result

Decisions = web.application(urls, locals());