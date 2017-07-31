from DBScrape import DBScrape
import calendar
import datetime
import time
import sys
import operator
class moveSuggestionGenerator:
	IE = {} #Individual Events
	TE = {} #Total Events
	ISP = {} #Individual Space Preference

	def backspace(self):
		print '\r',

	def scrapeData(self):
		databaseScrape=DBScrape()
		t = (2017, 4, 1, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, 60):
			s = str(round(float(i)/60.0*100.0,2)) + '%'
			print s,
			sys.stdout.flush()
			self.backspace()

			start = beginTime + i*24*60*60
			end = beginTime + (i+1)*24*60*60
			shots = databaseScrape.snapshots_col_users(start, end)

			currentEnergy = 0
			newEnergy = 0
			currentSpace = "Out of Lab"
			newSpace = "Out of Lab"

			for shot in shots:
				users = shot["data"]
				for user in users:
					personalData = users[user]
					energyValue = personalData["value"]
					location = personalData["location"]

					currentEnergy = newEnergy
					newEnergy = energyValue #shift new energy values
					currentSpace = newSpace
					newSpace = location #shift new location

					if (currentSpace == "Out of Lab" or newSpace == "Out of Lab" or currentSpace == "outOfLab" or newSpace == "outOfLab"):
						continue
					if (currentSpace == newSpace):
						continue
					locationTuple = (currentSpace, newSpace)
					energyDiff = newEnergy - currentEnergy

					if (user not in self.IE): #instantiate individual events if needed
						self.IE[user] = {}
					if (locationTuple not in self.IE[user]):
						self.IE[user][locationTuple] = [energyDiff]
					else:
						self.IE[user][locationTuple].append(energyDiff)





					if (locationTuple not in self.TE): #instantiate total events if needed
						self.TE[locationTuple] = [energyDiff]
					else:
						self.TE[locationTuple].append(energyDiff)




					if (user not in self.ISP): #instantiate individual space preferences if needed
						self.ISP[user] = {}
					if (location not in self.ISP[user]):
						self.ISP[user][location] = 1
					else:
						self.ISP[user][location] += 1

	def getStatistics(self):
		for action in self.TE:
			listLen = len(self.TE[action])
			if (listLen < 1000):
				continue
			avg = sum(self.TE[action])/float(listLen)
			if (avg > 0):
				continue
			sList = sorted(self.TE[action])
			print action[0],
			print " to ",
			print action[1],
			print ", total: ",
			print listLen,
			print ", average: ",
			print avg,
			print ", median: ",
			print sList[listLen/2]

		print "\n\n===================================\nIndividual Space Preferences\n"

		for user in self.ISP:
			locations = self.ISP[user]
			print user,
			sortedLocations = sorted(locations.items(), key=operator.itemgetter(1))
			print sorted[0:3]


M = moveSuggestionGenerator()
M.scrapeData()
M.getStatistics()













