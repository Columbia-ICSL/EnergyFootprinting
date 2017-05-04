import DBScrape
import csv
import os
import argparse
import calendar
import datetime


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", help="how many days back to start scrape", type=int)
parser.add_argument("-e", "--end", help="how many days back to end scrape", type=int)
parser.add_argument("-o", "--offset", help="how many hours to offset scrape", type=int)
parser.add_argument('-u', "--userID", help="user ID", type=str)
args = parser.parse_args()


#set defaults
end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60 #1 day
hours = 0
if (args.start):
	start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*args.start
if (args.end):
	end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*args.end
assert(start < end)

if (args.offset):
	start += 60*60*args.offset
	end += 60*60*args.offset

print(datetime.datetime.fromtimestamp(start))
print(datetime.datetime.fromtimestamp(end))

userID = "9432F0A3-660D-4C35-AA63-C7CFDD6D0F4D"
if (args.userID):
	userID = args.userID

try:
    os.remove('userSnapshots.csv')
except OSError:
    pass

db=DBScrape.DBScrape()

users = db.registration_col1()
shots = db.snapshots_col_users(start, end)

with open('userSnapshots.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	writeArray = []
	writeArray += ["year", "month", "day", "hour", "minute", "second", "HVAC", "Light", "Electric"]
	spamwriter.writerow(writeArray)
	for shot in shots:
		D = shot["timestamp"]
		userList = shot["data"]
		writeArray = []
		writeArray.append(D.year)
		writeArray.append(D.month)
		writeArray.append(D.day)
		writeArray.append(D.hour)
		writeArray.append(D.minute)
		writeArray.append(D.second)	
		A = {"HVAC":0, "Light":0, "Electrical":0}
		if userID in userList:
			writeArray.append(userList[userID]["location"])
			consumptions = userList[userID]["consumptions"]
			for device in consumptions:
				A[device["type"]] += device["share"]
		else:
			writeArray.append("Out of Lab")
		writeArray.append(A["HVAC"])
		writeArray.append(A["Light"])
		writeArray.append(A["Electrical"])
		spamwriter.writerow(writeArray)
#	for person in users:
#		personID = person["userID"]
#		writeArray.append(personID)
#	spamwriter.writerow(writeArray)
#
#	for shot in shots:
#		D = shot["timestamp"]
#		userList = shot["data"]
#		writeArray = []
#		writeArray.append(D.year)
#		writeArray.append(D.month)
#		writeArray.append(D.day)
#		writeArray.append(D.hour)
#		writeArray.append(D.minute)
#		writeArray.append(D.second)
#		if 
#		for person in users:
#			userFound = False
#			personID = person["userID"]
#			if personID in userList:
#				consumptions = userList[personID]["value"]
#				for 
#				writeArray.append(userList[personID]["value"])
#				userFound = True
#				continue
#			if (not userFound):
#				writeArray.append(0)

#		spamwriter.writerow(writeArray)

