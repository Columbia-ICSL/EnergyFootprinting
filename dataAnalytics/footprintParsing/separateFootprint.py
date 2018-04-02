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

	def printC(self, text):
		if self.verbose:
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


			self.timestamps.append(timestamp)
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
		return self.footprints

	def getTimestamps(self):
		return self.timestamps

	def getRoomFootprint(self, room):
		if room not in self.footprints:
			return None
		else:
			return self.footprints[room]

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



class getParameters:
	def __init__(self, verbose):
		self.databaseScrape = DBScrape.DBScrape()
		self.verbose = verbose
		self.timestamps = []
		self.parameter = []

	def printC(self, text):
		if self.verbose:
			print text

	def getParameter(self, p, beginYear, beginMonth, beginDay, endYear, endMonth, endDay):
		self.parameter = []
		begin = datetime.datetime(beginYear, beginMonth, beginDay)
		end = datetime.datetime(endYear, endMonth, endDay)
		begin = calendar.timegm(begin.utctimetuple())
		end = calendar.timegm(end.utctimetuple())

		shots = self.databaseScrape.snapshots_parameters(begin, end)
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
			self.timestamps.append(timestamp)
			if p in shot["data"]:
				self.parameter.append(shot["data"][p])
		self.saveTimeSeries(p)
		return self.parameter

	def saveTimeSeries(self, p):
		filename = p + '.csv'
		try:
			os.remove(filename)
		except OSError:
			pass
		with open(filename, 'wb') as csvfile:
			footprintWriter = csv.writer(csvfile, delimiter=' ',
				quotechar=' ', quoting=csv.QUOTE_MINIMAL)
			footprintWriter.writerow(["timestamps"] + self.timestamps)
			footprintWriter.writerow([p] + self.parameter)
