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


os.remove('registration_col1.csv')
db=DBScrape.DBScrape()

users = db.registration_col1()
shots = db.snapshots_col_rooms(start, end)

with open('registration_col1.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for shot in shots:
		roomList = shot["data"]
		writeArray = []
		for person in users:
			spaceFound = False
			personID = person["userID"]
			for room in roomList:
				if personID in room["users"]:
					writeArray.append(room["name"])
					spaceFound = True
					break
			if (not spaceFound):
				writeArray.append("None")
		writeArray.append(room)

		spamwriter.writerow(writeArray)

