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
    os.remove('applianceUsers.csv')
    os.remove('applianceEnergy.csv')
except OSError:
    pass

db=DBScrape.DBScrape()

shots = db.snapshots_col_appliances(start, end)

firstShot = shots[0]
applianceList = list(firstShot["data"].keys())


with open('applianceUsers.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	writeArray = []
	for appliance in applianceList:
		writeArray.append(appliance)
	spamwriter.writerow(writeArray)

	for shot in shots:
		D = shot["timestamp"]
		shotAppliances = shot["data"]
		writeArray = []
		writeArray.append(D.year)
		writeArray.append(D.month)
		writeArray.append(D.day)
		writeArray.append(D.hour)
		writeArray.append(D.minute)
		writeArray.append(D.second)
		for appliance in applianceList:
			applianceFound = False
			if appliance in shotAppliances:
				writeArray.append(shotAppliances[appliance]["total_users"])
				applianceFound = True
				continue
			if (not applianceFound):
				writeArray.append(0)

		spamwriter.writerow(writeArray)

with open('applianceEnergy.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	writeArray = []
	writeArray += ["year", "month", "day", "hour", "minute", "second"]
	for appliance in applianceList:
		writeArray.append(appliance)
	spamwriter.writerow(writeArray)

	for shot in shots:
		D = shot["timestamp"]
		shotAppliances = shot["data"]
		writeArray = []
		writeArray.append(D.year)
		writeArray.append(D.month)
		writeArray.append(D.day)
		writeArray.append(D.hour)
		writeArray.append(D.minute)
		writeArray.append(D.second)
		for appliance in applianceList:
			applianceFound = False
			if appliance in shotAppliances:
				writeArray.append(shotAppliances[appliance]["value"])
				applianceFound = True
				continue
			if (not applianceFound):
				writeArray.append(0)

		spamwriter.writerow(writeArray)

