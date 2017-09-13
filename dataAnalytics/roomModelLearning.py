import DBScrape
import calendar
import datetime
import time
import csv
import sys
import os

days = 30
class roomModelLearning:
	energyDictionary = {}
	energyCounts = {}

	occupancyDictionary = {}
	occupancyCounts = {}
	def backspace(self):
		print '\r',

	def roomEnergyLearning(self):
		databaseScrape = DBScrape.DBScrape()
		t = (2017, 3, 15, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, days):
			s = str(round(float(i)/days*100.0)) + '%'
			print s,
			sys.stdout.flush()
			self.backspace()
			start = beginTime + i*24*60*60
			end = beginTime + (i+1)*24*60*60
			shots = databaseScrape.snapshots_col_appliances(start, end)

			for snapshot in shots:
				timestamp = snapshot["timestamp"]
				timestamp = calendar.timegm(timestamp.utctimetuple())
				b = int(timestamp-start)/900
				day = b/96
				binNumber = b%96
				data = snapshot["data"]
				for appliance in data:
					params = data[appliance]
					if (type(params) == type(150)):
						continue
					energy = params["value"]
					rooms = params["rooms"]
					l = len(rooms)
					for room in rooms:
						if room not in self.energyDictionary:
							self.energyDictionary[room] = [[0]*96 for index in range(days)]
							self.energyCounts[room] = [[0]*96 for index in range(days)]
						if (day >= days or binNumber >= 96):
							print((binNumber, day))
							continue
						self.energyDictionary[room][day][binNumber] += energy
				for room in self.energyDictionary:
					self.energyCounts[room][day][binNumber] += 1

	def roomOccupancyLearning(self):
		databaseScrape = DBScrape.DBScrape()
		t = (2017, 3, 15, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, days):
			s = str(round(float(i)/days*100.0)) + '%'
			print s,
			sys.stdout.flush()
			self.backspace()
			start = beginTime + i*24*60*60
			end = beginTime + (i+1)*24*60*60
			shots = databaseScrape.snapshots_col_rooms(start, end)

			for snapshot in shots:
				timestamp = snapshot["timestamp"]
				timestamp = calendar.timegm(timestamp.utctimetuple())
				b = int(timestamp-start)/900
				day = b/96
				binNumber = b%96
				data = snapshot["data"]
				for room in data:
					params = data[room]
					if (type(params) == type(150)):
						continue
					occupancy = len(params["users"])
					if room not in self.occupancyDictionary:
						self.occupancyDictionary[room] = [[0]*96 for index in range(days)]
						self.occupancyCounts[room] = [[0]*96 for index in range(days)]
					if (day >= days or binNumber >= 96):
						print((binNumber, day))
						continue
					self.occupancyDictionary[room][day][binNumber] += occupancy
				for room in self.energyDictionary:
					self.energyCounts[room][day][binNumber] += 1

	def saveEnergyData(self):
		try:
			os.remove('savedRoomEnergyData.csv')
		except OSError:
			pass
		with open('savedRoomEnergyData.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for room in self.energyDictionary:
				arr = self.energyDictionary[room]
				arrCount = self.energyCounts[room]
				savedArray = [0]*96*days

				for i in range(days):
					for j in range(96):
						if (arrCount[i][j] > 1):
							savedArray[i*96 + j] += arr[i][j]/arrCount[i][j]
						else:
							savedArray[i*96 + j] += arr[i][j]
				spamwriter.writerow(room)
				spamwriter.writerow(savedArray)

	def saveOccupancyData(self):
		try:
			os.remove('savedRoomOccupancyData.csv')
		except OSError:
			pass
		with open('savedRoomOccupancyData.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for room in self.occupancyDictionary:
				arr = self.occupancyDictionary[room]
				arrCount = self.occupancyCounts[room]
				savedArray = [0]*96*days

				for i in range(days):
					for j in range(96):
						if (arrCount[i][j] > 1):
							savedArray[i*96 + j] += arr[i][j]/arrCount[i][j]
						else:
							savedArray[i*96 + j] += arr[i][j]
				spamwriter.writerow(room)
				spamwriter.writerow(savedArray)

R = roomModelLearning()
R.roomEnergyLearning()
R.saveEnergyData()
R.roomOccupancyLearning()
R.saveOccupancyData()



