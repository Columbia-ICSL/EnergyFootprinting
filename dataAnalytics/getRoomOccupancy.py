import DBScrape
import calendar
import datetime
import time
import csv
import sys
import os



class getRoomOccupancy:

	def __init__(self):
		self.databaseScrape = DBScrape.DBScrape()
		self.timestamps = []
		self.occupancyDictionary = {}

	def backspace(self):
		print '\r',
	
	def getOccupancy(self, year, startMonth, startDay = 1, days = 1):
		t = (year, startMonth, startDay, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, days):
			s = str(round(float(i)/days*100.0)) + '%'
			print s,
			sys.stdout.flush()
			self.backspace()
			start = beginTime + i*24*60*60
			end = beginTime + (i+1)*24*60*60
			shots = self.databaseScrape.snapshots_col_appliances(start, end)
			for snapshot in shots:
				timestamp = snapshot["timestamp"]
				timestampFormatted = time.strftime("%d-%b-%Y %H:%M:%S", timestamp.utctimetuple())
				self.timestamps.append(timestampFormatted)

				data = snapshot["data"]

				for room in data:
					params = data[room]
					if (type(params) == type(150)):
						continue
					occupancy = len(params["users"])
					if room not in self.occupancyDictionary:
						self.occupancyDictionary[room] = []
						self.occupancyCounts[room] = []

					self.occupancyDictionary[room].append(occupancy)

	def saveData(self):
		if not os.path.exists('occupancyCSVFiles'):
			os.makedirs('occupancyCSVFiles')
		try:
			os.remove('occupancyCSVFiles/roomOccupancy.csv')
		except OSError:
			pass
		with open('occupancyCSVFiles/roomOccupancy.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)

			for room in self.occupancyDictionary:
				roomArray = []
				roomArray.append(room)
				for occupancy in self.occupancyDictionary[room]:
					roomArray.append(occupancy)
				spamwriter.writerow(roomArray)

	def saveTimestamps(self):
		if not os.path.exists('occupancyCSVFiles'):
			os.makedirs('occupancyCSVFiles')
		try:
			os.remove("occupancyCSVFiles/occupancyTimestamps.csv")
		except OSError:
			pass
		with open("occupancyCSVFiles/occupancyTimestamps.csv", 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter = ',',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			spamwriter.writerow(self.timestamps)



G = getRoomOccupancy()
G.getOccupancy(2017, 9, 1, 30)
G.saveData()
G.saveTimestamps()

