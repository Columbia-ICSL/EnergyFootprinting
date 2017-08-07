import DBScrape
import calendar
import datetime
import time
import csv
import os

class roomAnalytics:
	energyDictionary = {}
	def roomData(self):
		databaseScrape = DBScrape.DBScrape()
		t = (2017, 4, 1, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, 60):
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
					energy = params["value"]
					rooms = params["rooms"]
					l = len(rooms)
					for room in rooms:
						if room not in self.energyDictionary:
							self.energyDictionary[room] = [[0]*96 for index in range(60)]
						if (day >= 60 or binNumber >= 96):
							print((binNumber, day))
							continue
						self.energyDictionary[room][day][binNumber] += energy/l


	def saveData(self):
		try:
			os.remove('savedData.csv')
		except OSError:
			pass
		with open('savedData.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			writeArray = []
			for room in energyDictionary:
				if (room != "nwc1003b_a"):
					continue
				arr = energyDictionary[room]
				spamwriter.writerow(arr[30])
				savedArray = [0]*96

				for i in range(96):
					for j in range(60):
						savedArray[i] += arr[j][i]
				for k in range(96):
					savedArray[k] = savedArray[k]/96
				spamwriter.writerow(savedArray)









R = roomAnalytics()
R.roomData()
R.saveData()