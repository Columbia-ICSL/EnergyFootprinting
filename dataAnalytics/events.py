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

userID = "9432F0A3-660D-4C35-AA63-C7CFDD6D0F4D"
if (args.userID):
	userID = args.userID

try:
    os.remove('locationChangeEvents.csv')
#    os.remove('occupancyChangeEvents.csv')
except OSError:
    pass

db=DBScrape.DBScrape()

#shots = db.snapshots_col_appliances(start, end)
users = db.registration_col1()
user_shots = db.snapshots_col_users(start, end)

#appliance_shots = db.snapshots_col_appliances(start, end)
#firstShot = appliance_shots[0]
#applianceList = list(firstShot["data"].keys())


with open('locationChangeEvents.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
#with open('occupancyChangeEvents.csv', 'wb') as csvfileO:
#	occupancyWriter = csv.writer(csvfileO, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	writeArray = []
#	occupancyArray = []
	writeArray += ["year", "month", "day", "hour", "minute", "second", "oldLocation", "location", "oldOccupancy", "occupancy", "oldValue", "value"]
	spamwriter.writerow(writeArray)
#	occupancyArray += ["year", "month", "day", "hour", "minute", "second", "oldOccupancy", "occupancy", "oldValue", "value"]
#	occupancyWriter.writerow(occupancyArray)
	oldValue = 0
	newValue = 0
	oldLocation = "outOfLab"
	newLocation = "outOfLab"
	oldOccupancy = 0
	newOccupancy = 0
	for shot in user_shots:
		D = shot["timestamp"]
		userList = shot["data"]
		writeArray = []
		occupancyArray = []
		if (userID in userList):
			oldLocation = newLocation
			newLocation = userList[userID]["location"]
			oldValue = newValue
			newValue = userList[userID]["value"]
			if ((oldLocation == "outOfLab") or (newLocation == "outOfLab")):
				continue

			occupancy = 0
			for userID in userList:
				if (userList[userID]["location"] == newLocation):
					occupancy += 1
			assert(occupancy != 0)
			oldOccupancy = newOccupancy
			newOccupancy = occupancy

			if ((oldLocation != newLocation) or (oldOccupancy != newOccupancy)):
				if (oldOccupancy == 0):
					continue
				assert(newOccupancy != 0)
				writeArray.append(D.year)
				writeArray.append(D.month)
				writeArray.append(D.day)
				writeArray.append(D.hour)
				writeArray.append(D.minute)
				writeArray.append(D.second)
				writeArray.append(oldLocation)
				writeArray.append(newLocation)
				writeArray.append(oldOccupancy)
				writeArray.append(occupancy)
				writeArray.append(oldValue)
				writeArray.append(newValue)
				spamwriter.writerow(writeArray)


			

