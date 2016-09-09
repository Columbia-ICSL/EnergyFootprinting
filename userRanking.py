import json
import web
import cloudserver

urls = (
	"/", "ranking")

class ranking:
	def POST(self):
		raw_data=web.data()
		userID = cloudserver.db.userIDLookup(raw_data)
		json_return = {
			"user":userID,
			"balance": cloudserver.db.getUserBalance(userID),
			"rank":0,
			"rankingData":[]
		}
		def make_entry(user, balance, Others={}):
			Others.update({
				"user":user,
				"balance":balance
				})
			return Others
		rankingData = cloudserver.db.getRankingData()
		i = 0
		for rank in rankingData:
			i += 1
			attributes = cloudserver.db.getAttributes(rank["user"], False)
			user = rank["user"]	
			if (attributes["public"] == False):
				rank["user"] = "anonymous"
			balance = rank["balance"]
			if (userID == user):
				json_return["rank"] = i
			json_return["rankingData"].append(rank)
		return cloudserver.db._encode(json_return, False)

	def GET(self):
		json_return = {
			"rankingData":[]
		}
		rankingData = cloudserver.db.getRankingData()
		for rank in rankingData:
			user = rank["user"]
			balance = rank["balance"]
			json_return["rankingData"].append(rank)
		return cloudserver.db._encode(json_return, False)

userRankings = web.application(urls, locals());