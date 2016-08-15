import json
import web
import cloudserver

urls = (
"/","DecisionVals")

class DecisionVals:
	def POST(self):
        raw_data=web.data()
        data = raw_data.split(',')
        action = data[1]
        if (action == "accept"):
        	return "accepted"
        elif (action == "decline"):
        	return "declined"
        return "what"

    def GET(self):
        return result

Decisions = web.application(urls, locals());