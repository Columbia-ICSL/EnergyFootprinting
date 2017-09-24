import DBScrape
import calendar
import datetime
import time
import csv
import sys
import os

class getHVACparameters():
	timestamps = []
	parameters = ["hfr10T1", "energy1003GA", "energy1003GC", "energy1003GB", "energy10T1", "hfr1003o1", "energy8F", "energy1003G", "energy1003B", "energy1003A", "exhaust10T1", "exhaust10M1", "exhaust10M3", "exhaust10M2", "hfr7F", "energy1001L", "energy7F", "hfr1003GA", "hfr1003GB", "hfr1003GC", "exhaust1001L", "hfr10F", "hfr8F", "energy1003t2", "T2temp", "hfr1003t2", "exhaust1003GB", "exhaust1003G", "hfr1003g", "exhaust1003GA", "T1temp", "energy10F", "hfr1003A", "hfr1003B", "exhaust1003GC", "energy1003o1", "exhaust10S5", "exhaust10S4", "hfr1001L", "1003airTemp", "1003airFlow", "10T1airTemp", "10T1airFlow"]
	values = []
	def params(self):
		databaseScrape = DBScrape.DBScrape()
		end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
		start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*5 #5 days
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
				ind = self.parameters.index(param)
				self.values[valueTime][ind] = data[param]
			valueTime += 1

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
H.params()
H.saveData()
H.saveTimestamps()





