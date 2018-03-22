import datetime
import os
import calendar
import time
import csv

#change to the path containing DBScrape.py.
import DBScrape



class getFootprints:
	def __init__(self, S, verbose):
		self.verbose = verbose
		self.databaseScrape = DBScrape.DBScrape()
		self.timestamps = []
		self.footprints = {}
		self.spaces = S
		print("Found " + str(len(self.spaces)) + " spaces")
		for room in self.spaces:
			self.footprints[room] = []

	def printC(text):
		if verbose:
			print text
	
	def getSnapshots(self, beginYear, beginMonth, beginDay, endYear, endMonth, endDay):
		begin = datetime.datetime(beginYear, beginMonth, beginDay)
		end = datetime.datetime(endYear, endMonth, endDay)
		begin = calendar.timegm(begin.utctimetuple())
		end = calendar.timegm(end.utctimetuple())

		shots = self.databaseScrape.snapshots_col_appliances(begin, end)
		self.printC("Found " + str(len(shots)) + " snapshots")
		for shot in shots:
			timestamp = shot["timestamp"]
			pattern1 = '%Y-%m-%d %H:%M:%S.%f'
			pattern2 = '%Y-%m-%d %H:%M:%S'
			self.printC(timestamp)
			try:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern1)))
			except ValueError:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern2)))


			self.timestamps.append(epoch)
			for room in self.spaces:
				self.footprints[room].append(0)

			for applianceName in shot["data"]:
				appliance = shot["data"][applianceName]
				rooms = appliance["rooms"]
				numRooms = len(rooms)
				for room in rooms:
					if room not in self.footprints:
						print "room " + room + " not in space database"
						continue
					self.footprints[room][-1] = self.footprints[room][-1] + appliance["value"]/numRooms

	def saveTimeSeries(self):
		try:
			os.remove('footprints.csv')
		except OSError:
			pass
		with open('footprints.csv', 'wb') as csvfile:
			footprintWriter = csv.writer(csvfile, delimiter=' ',
					quotechar=' ', quoting=csv.QUOTE_MINIMAL)
			footprintWriter.writerow(["timestamps"] + self.timestamps)
			for room in self.footprints:
				footprintWriter.writerow([room] + self.footprints[room])




