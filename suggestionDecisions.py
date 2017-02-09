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
		messageID = data[1]
		cloudserver.db.submitAcceptedSuggestion(deviceID, messageID)
		cloudserver.db.recordEvent(user, "suggestion received", messageID)
		cloudserver.db.pushManagementDispUpdate(messageID)
		coins = int(data[2])
		cloudserver.db.updateUserBalance(deviceID, coins)
		return "success"

	def GET(self):
		return result

Decisions = web.application(urls, locals());