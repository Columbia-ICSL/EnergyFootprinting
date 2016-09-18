import DBMgr
import datetime
import csv
import time

db=DBMgr.DBMgr()

nowTime = datetime.datetime.now().replace(hour=4, minute=0)
print("4AM today: " + str(nowTime))
curtime = int(time.mktime(nowTime.timetuple()))
dict_users = cloudserver.db.BinUsersLocHistory(curtime-86400, curtime)
numUsers = [0, 0, 0, 0, 0]
userDict = {}
with open('changeSchedule.csv', 'w') as csvfile:
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
		userName = cloudserver.db.userIDLookup(user_id)
		user_list.append(userName)
		return_bins = dict_users[user_id]
		for bin_start in sorted(return_bins.keys()):
			BIN_ST = return_bins[bin_start]
			if (BIN_ST["value"] == None):
				user_list.append(0)
			else:
				user_list.append(BIN_ST["value"])
		writer.writerow(user_list)