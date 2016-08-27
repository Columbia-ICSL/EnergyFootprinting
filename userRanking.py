import json
import web
import cloudserver

urls = (
	"/", "ranking")

class ranking:
	def POST(self):
		raw_data=web.data()
		json_return = {
			"user":cloudserver.db.userIDLookup(raw_data),
			"balance": 0,
			"rankingData":[]
		}
		def make_entry(user, balance, Others={}):
			Others.update({
				"user":user,
				"balance":balance
				})
			return Others
		rankingData = cloudserver.db.getRankingData()
		for rank in rankingData:
			user = rank["user"]
			balance = rank["balance"]
			json_return["rankingData"].append(make_entry(user, balance))
		return cloudserver.db._encode(json_return, False)

	def GET(self):
		return

userRankings = web.application(urls, locals());