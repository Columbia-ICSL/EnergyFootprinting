import pymongo
import datetime
import os
import csv

class getLocationTrainingTestingData():
	def __init__(self):
		self.dbc=pymongo.MongoClient()
		return

	def getTrainingData(self):
		self.humanCentricZones=self.dbc.db.humanCentricZones
		trainingData = list(self.humanCentricZones.find())
		try:
			os.remove('trainingData.csv')
		except OSError:
			pass
		with open('trainingData.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
						quotechar='|', quoting=csv.QUOTE_MINIMAL)
			writeArray = []
			writeArray += ["x", "y"]
			for i in range(41):
				writeArray.append("b" + str(i))
			spamwriter.writerow(writeArray)

			for data in trainingData:
				x = data["x"]
				y = data["y"]
				beacons = data["beacons"]
				writeArray = []
				writeArray += [x, y]
				assert(len(beacons) == 41)
				for j in len(beacons):
					writeArray.append(beacons[j])
				spamwriter.writerow(writeArray)


	def getTestingData(self):
		self.humanCentricZonesTesting=self.dbc.db.humanCentricZonesTesting
		testingData = list(self.humanCentricZonesTesting.find())
		try:
			os.remove('testingData.csv')
		except OSError:
			pass
		with open('trainingData.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
			writeArray = []
			for i in range(41):
				writeArray.append("b" + str(i))
			spamwriter.writerow(writeArray)

			for data in testingData:
				beacons = data["beacons"]
				writeArray = []
				assert(len(beacons) == 41)
				for j in len(beacons):
					writeArray.append(beacons[j])
				spamwriter.writerow(writeArray)


training = getLocationTrainingTestingData()
training.getTrainingData()
training.getTestingData()
