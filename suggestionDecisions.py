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
		print("\nDecision received from " + deviceID + "of length " + str(len(data)) + "\n")
		user = cloudserver.db.userIDLookup(deviceID)
		messageID = data[1]
		if len(data) > 3:
			testString = data[3]
			print("\nThe teststring is " + testString+ "\n")
			if testString.lower() == "true":
				accepted = True
				print("\n An Accepted sugestion has been detected")
			else:
				accepted = False
				print("\n A rejected suggestion has been detected")
			cloudserver.db.submitAcceptedSuggestion(deviceID, messageID, accepted)
		else:
			cloudserver.db.submitAcceptedSuggestion(deviceID, messageID)
		cloudserver.db.recordEvent(user, "suggestion received", messageID)
		cloudserver.db.pushManagementDispUpdate(messageID)
		cloudserver.RS.clearRecs(user, messageID)
		coins = int(data[2])
		cloudserver.db.updateUserBalance(deviceID, coins)
		return "success"

	def GET(self):
		return result

Decisions = web.application(urls, locals());
