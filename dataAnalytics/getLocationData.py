import DBScrape
import datetime
import time
import csv
import sys
import os

class getLocationData:
	def __init__(self):
		self.databaseScrape = DBScrape.DBScrape()
		self.locationDict = {}

	def getSnapshots(self):
		begin = datetime.datetime(2017, 2, 1)
		dayTime = begin
		dayTomorrow = dayTime + datetime.timedelta(days=1)
		while dayTime < dayTime.now():
			shots = self.databaseScrape.snapshots_col_users(dayTime, dayTomorrow)
			for snapshot in shots:
				timestamp = snapshot["timestamp"]
				data = snapshots["data"]
				for user in data:
					person = user
					location = data[user]["location"]
					if (person not in self.locationDict):
						self.locationDict[person] = []
					self.locationDict[person].append((timestamp, location))
			dayTime = dayTime + datetime.timedelta(days=1)
			dayTomorrow = dayTime + datetime.timedelta(days=1)
			time.sleep(5)
			print(dayTime)

	def saveData(self):
		if not os.path.exists('locationDataFiles'):
			os.makedirs('locationDataFiles')
		try:
			os.remove('locationDataFiles/locationData.csv')
		except OSError:
			pass
		with open('locationDataFiles/locationData.csv') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			L = len(self.locationDict)
			i = 0
			print("Storing location data")
			for person in self.locationDict:
				i += 1
				print str(i/L) + "%"
				timestamps = []
				locations = []
				for tup in self.locationDict[person]:
					timestamps.append(tup[0])
					locations.append(tup[1])
				spamwriter.writerow(timestamps)
				spamwriter.writerow(locations)


G = getLocationData()
G.getSnapshots()
G.saveData()