import sys
import DBScrape
import calendar
import datetime
import time
import csv
import sys
import os

args = list(sys.argv)[1:]
if len(args) != 2:
	raise Exception("Need 2 arguments: how many days back, how long")

class getHVACparameters():
	timestamps = []
	parameters = ["hfr10T1", "energy1003GA", "energy1003GC", "energy1003GB", "energy10T1", "hfr1003o1", "energy8F", "energy1003G", "energy1003B", "energy1003A", "exhaust10T1", "exhaust10M1", "exhaust10M3", "exhaust10M2", "hfr7F", "energy1001L", "energy7F", "hfr1003GA", "hfr1003GB", "hfr1003GC", "exhaust1001L", "hfr10F", "hfr8F", "energy1003t2", "T2temp", "hfr1003t2", "exhaust1003GB", "exhaust1003G", "hfr1003g", "exhaust1003GA", "T1temp", "energy10F", "hfr1003A", "hfr1003B", "exhaust1003GC", "energy1003o1", "exhaust10S5", "exhaust10S4", "hfr1001L", "1003airTemp", "1003airFlow", "10T1airTemp", "10T1airFlow", "T2setpoint", "T1setpoint", "1003GairFlow", "1003GairTemp", "1003GAairFlow", "1003GAairTemp", "1003GBairFlow", "1003GBairTemp", "1003GCairFlow", "1003GCairTemp", "1003daninoAT", "1003daninoAF", "1003AairTemp", "1003AairFlow", "1003BairTemp", "1003BairFlow", "1001LairTemp", "1001LairFlow", "10o1temp", "10o1stpt", "1001Ltemp", "1001Lstpt", "10L3temp", "10L3stpt", "10M4temp", "10M4stpt"]
	values = []
	paramValue = []
	paramTimestamps = []

	def getAllParams(self, daysBack, duration):
		self.params(daysBack, duration)
		self.saveData()
		self.saveTimestamps()

	def getSingleParam(self, parameter, xdays):
		self.paramsVal(parameter, xdays)
		self.saveSingleData()
		self.saveSingleTimestamps()

	def paramsVal(self, parameter, xdays):
		databaseScrape = DBScrape.DBScrape()
		end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*xdays #x days
		shots = databaseScrape.snapshots_parameters(start, end)

		valueTime = 0
		for snapshot in shots:
			timestamp = snapshot["timestamp"]
			timestamp = time.strftime("%d-%b-%Y %H:%M:%S", timestamp.utctimetuple())
			data = snapshot["data"]
			if (parameter not in data):
				print parameter + "missing"
				continue
			self.paramValue.append(data[parameter])
			self.paramTimestamps.append(timestamp)

	def params(self, daysBack, duration):
		databaseScrape = DBScrape.DBScrape()
		end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*(daysBack-duration)
		start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*daysBack #5 days
		shots = databaseScrape.snapshots_parameters(start, end)

		valueTime = 0
		for snapshot in shots:
			timestamp = snapshot["timestamp"]
			#timestamp = calendar.timegm(timestamp.utctimetuple())
			timestamp = time.strftime("%d-%b-%Y %H:%M:%S", timestamp.utctimetuple())
			self.timestamps.append(timestamp)
			self.values.append([0] * len(self.parameters))
			data = snapshot["data"]
			for param in data:
				if param not in self.parameters:
					print param + " missing"
					continue
				ind = self.parameters.index(param)
				self.values[valueTime][ind] = data[param]
			valueTime += 1

	def saveSingleData(self):
		try:
			os.remove('HVACparams.csv')
		except OSError:
			pass
		with open('HVACparams.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			spamwriter.writerow(self.paramValue)

	def saveSingleTimestamps(self):
		try:
			os.remove("HVACparamsTimestamps.csv")
		except OSError:
			pass
		with open("HVACparamsTimestamps.csv", 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			spamwriter.writerow(self.paramTimestamps)

	def saveData(self):
		try:
			os.remove('HVACparams.csv')
		except OSError:
			pass
		with open('HVACparams.csv', 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=' ',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			spamwriter.writerow(self.parameters)
			for T in range(len(self.values)):
				spamwriter.writerow(self.values[T])

	def saveTimestamps(self):
		try:
			os.remove("HVACparamsTimestamps.csv")
		except OSError:
			pass
		with open("HVACparamsTimestamps.csv", 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			spamwriter.writerow(self.timestamps)

H = getHVACparameters()
H.getAllParams(int(args[0]), int(args[1]))
#H.getSingleParam("10T1airTemp", 15)





