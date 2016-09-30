import web
import datetime
import time
import calendar
import json
import DBMgr

import cloudserver

urls = (
	"/binAllUsers/", "binAllUsers",
	"/binRoomOccupancy/", "binRoomOccupancy",
	"/binAppliancePower/", "binAppliancePower")

class binAllUsers:
	def GET(self):
		raw_time = web.input()
		if "end" not in raw_time:
			end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		else:
			end = float(raw_time['end'])
		if "start" not in raw_time:
			start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
		else:
			start = float(raw_time['start'])
		dict_users = cloudserver.db.BinUsersLocHistory(start, end)
		json_return = {}

		for user_id in dict_users:
			user_list = []
			return_bins = dict_users[user_id]
			for bin_start in sorted(return_bins.keys()):
				BIN_ST = return_bins[bin_start]
				if (BIN_ST["value"] == None):
					user_list.append(0)
				else:
					user_list.append(BIN_ST["value"])
			json_return[user_id] = user_list
		return cloudserver.db._encode(json_return, False)

class binRoomOccupancy:
	def GET(self):
		json_return = {}
		raw_time = web.input()
		if "end" not in raw_time:
			end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		else:
			end = float(raw_time['end'])
		if "start" not in raw_time:
			start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
		else:
			start = float(raw_time['start'])
		dict_appl = cloudserver.db.BinApplPowerHistory(start, end)

		appl_list = []
		for appl_id in dict_appl:
			appl_list = []
			return_bins = dict_appl[appl_id]
			for bin_start in sorted(return_bins.keys()):
				BIN_ST = return_bins[bin_start]
				if (BIN_ST["avg_users"] == None):
					appl_list.append(0)
				else:
					appl_list.append(BIN_ST["avg_users"])
			json_return[appl_id] = appl_list
		return cloudserver.db._encode(json_return, False)

class binAppliancePower:
	def GET(self):
		json_return = {}
		raw_time = web.input()
		if "end" not in raw_time:
			end=calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		else:
			end = float(raw_time['end'])
		if "start" not in raw_time:
			start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60
		else:
			start = float(raw_time['start'])
		dict_appl = cloudserver.db.BinApplPowerHistory(start, end)

		appl_list = []
		for appl_id in dict_appl:
			appl_list = []
			return_bins = dict_appl[appl_id]
			for bin_start in sorted(return_bins.keys()):
				BIN_ST = return_bins[bin_start]
				if (BIN_ST["value"] == None):
					appl_list.append(0)
				else:
					if (BIN_ST["value"] < 0 or BIN_ST["value"] > 5000):
						appl_list.append(0)
					else:
						appl_list.append(BIN_ST["value"])
			json_return[appl_id] = appl_list
		return cloudserver.db._encode(json_return, False)

visualization = web.application(urls, locals())