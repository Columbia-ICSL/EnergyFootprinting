import DBScrape
import csv
import os
import argparse
import calendar
import datetime
import dateutil.parser

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", help="how many days back to start scrape", type=int)
parser.add_argument("-e", "--end", help="how many days back to end scrape", type=int)
parser.add_argument("-o", "--offset", help="how many hours to offset scrape", type=int)
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
	for person in users:
		personID = person["name"]
		writeArray.append(personID)
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
		for person in users:
			userFound = False
			personID = person["userID"]
			if personID in userList:
				writeArray.append(userList[personID]["value"])
				userFound = True
				continue
			if (not userFound):
				writeArray.append(0)

		spamwriter.writerow(writeArray)

