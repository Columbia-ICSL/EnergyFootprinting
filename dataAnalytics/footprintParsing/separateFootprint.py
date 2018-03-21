import sys
import datetime
import os

#change to the path containing DBScrape.py.
import DBScrape
from spaceNames import S
#contains the spaces
print "This is the name of the script: ", sys.argv[0]
print "Number of arguments: ", len(sys.argv)
if len(sys.argv) != 7:
	print "Supply arguments to this script. Example: python separateFootprint.py {beginYear} {beginMonth} {beginDay} {endYear} {endMonth} {endDay}"
	assert(len(sys.argv) == 7)
verbose = True
def printC(text):
	if verbose:
		print text

parameters = sys.argv[1:]
for i in range(len(parameters)):
	parameters[i] = int(parameters[i])

class getFootprints:
	def __init__(self):
		self.databaseScrape = DBScrape.DBScrape()
		self.timestamps = []
		self.footprints = {}
		self.spaces = S
		print("Found " + str(len(self.spaces)) + " spaces")
		for room in self.spaces:
			self.footprints[room] = []

	def getSnapshots(self, beginYear, beginMonth, beginDay, endYear, endMonth, endDay):
		begin = datetime.datetime(beginYear, beginMonth, beginDay)
		end = datetime.datetime(endYear, endMonth, endDay)
		shots = self.databaseScrape.snapshots_col_appliances(begin, end)
		printC("Found " + str(len(shots)) + " snapshots")
		for shot in shots:
			timestamp = shot["timestamp"]
			pattern = '%Y-%m-%d %H:%M:%S'
			epoch = int(time.mktime(time.strptime(date_time, pattern)))
			self.timestamps.append(epoch)
			for room in self.spaces:
				self.spaces[room].append(0)

			for applianceName in shot["data"]:
				appliance = shot["data"][applianceName]
				rooms = appliance["rooms"]
				numRooms = len(rooms)
				for room in rooms:
					if room not in self.footprints:
						print "room " + room + " not in space database"
						continue
					self.spaces[room][-1] = self.spaces[room][-1] + appliance["value"]/numRooms

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
















GF = getFootprints()
GF.getSnapshots(parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5])
GF.saveTimeSeries()





