import json
import web
import cloudserver

urls = (
	"/", "ranking")

class ranking:
	def POST(self):
		raw_data=web.data()
		return cloudserver.db.getRankingData()

	def GET(self):
		return

userRankings = web.application(urls, locals());