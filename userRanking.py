import json
import web
import cloudserver

urls = (
	"/", "ranking")

class ranking:
	def POST(self):
		return "hello from ranking!"

	def GET(self):
		return

userRankings = web.application(urls, locals());