import DBMgr
import datetime
import csv
import time
import os

db=DBMgr.DBMgr()

n = int(raw_input("How many days back?").strip())

nowTime = datetime.datetime.now().replace(hour=4, minute=0)
print("4AM today: " + str(nowTime))
curtime = int(time.mktime(nowTime.timetuple()))-(n*86400)
dict_users = db.BinUsersLocHistory(curtime-86400, curtime)
userDict = {}
roomDict = {}
changeScheduleFile = 'changeScheduleTest.csv'
try:
    os.remove(changeScheduleFile)
except OSError:
    pass
with open(changeScheduleFile, 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=' ',
		quotechar='|', quoting=csv.QUOTE_MINIMAL)
	user_list = []
	user_list.append(0)
	return_bins = dict_users[dict_users.keys()[0]]
	for bin_start in sorted(return_bins.keys()):
		user_list.append(bin_start)
	writer.writerow(user_list)
	user_list = []
	for user_id in dict_users:
		user_list = []
		userName = db.userIDLookup(user_id)
		if userName == None:
			userName = user_id
		user_list.append(userName.strip())
		return_bins = dict_users[user_id]
		for bin_start in sorted(return_bins.keys()):
			BIN_ST = return_bins[bin_start]
			if (BIN_ST["value"] == None):
				user_list.append(0)
			else:
				user_list.append(BIN_ST["value"])
		writer.writerow(user_list)
print("wrote changeScheduleTest.csv")
curtime = int(time.mktime(nowTime.timetuple()))-(n*86400)
dict_appl = db.BinApplPowerHistory(curtime-86400, curtime)
applDict = {}
roomDict = {}
applianceFile = 'applianceVisualization.csv'
applianceUsersFile = 'applianceUsersVisualization.csv'
try:
    os.remove(applianceFile)
except OSError:
    pass
try:
    os.remove(applianceUsersFile)
except OSError:
    pass

with open(applianceFile, 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=' ',
		quotechar='|', quoting=csv.QUOTE_MINIMAL)
	appl_list = []
	appl_list.append(0)
	return_bins = dict_appl[dict_appl.keys()[0]]
	for bin_start in sorted(return_bins.keys()):
		appl_list.append(bin_start)
	writer.writerow(appl_list)
	appl_list = []
	for appl_id in dict_appl:
		appl_list = []
		applName = db.ApplIdToName(appl_id)
		if applName == None:
			applName = appl_id
		appl_list.append(applName.replace(" ", ""))
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
		writer.writerow(appl_list)
print("wrote applianceVisualization.csv")
with open(applianceUsersFile, 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=' ',
		quotechar='|', quoting=csv.QUOTE_MINIMAL)
	appl_list = []
	appl_list.append(0)
	return_bins = dict_appl[dict_appl.keys()[0]]
	for bin_start in sorted(return_bins.keys()):
		appl_list.append(bin_start)
	writer.writerow(appl_list)
	appl_list = []
	for appl_id in dict_appl:
		appl_list = []
		applName = db.ApplIdToName(appl_id)
		if applName == None:
			applName = appl_id
		appl_list.append(applName.replace(" ", ""))
		return_bins = dict_appl[appl_id]
		for bin_start in sorted(return_bins.keys()):
			BIN_ST = return_bins[bin_start]
			if (BIN_ST["avg_users"] == 0):
				appl_list.append(0)
			else:
				appl_list.append(BIN_ST["avg_users"])
		writer.writerow(appl_list)
print("wrote applianceUsersVisualization.csv")