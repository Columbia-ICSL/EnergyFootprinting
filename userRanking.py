import json
import web
import cloudserver

urls = (
	"/", "ranking")

class ranking:
	def POST(self):
		raw_data=web.data()
		return raw_data

	def GET(self):
		return

userRankings = web.application(urls, locals());