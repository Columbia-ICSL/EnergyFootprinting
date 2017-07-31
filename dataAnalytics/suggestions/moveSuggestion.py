from .. import DBScrape
import calendar
import datetime
import time
class moveSuggestionGenerator:
	IE = {} #Individual Events
	TE = {} #Total Events
	ISP = {} #Individual Space Preference

	def scrapeData(self):
		db=DBScrape.DBScrape()
		t = (2017, 4, 1, 0, 0, 0, 0, 0, 0)
		beginTime = calendar.timegm(datetime.datetime.utcfromtimestamp(time.mktime(t)).utctimetuple())
		for i in range(0, 60):
			start = beginTime + i*24*60*60
			end = beginTime + (i+1)*24*60*60
			shots = db.snapshots_col_users(start, end)

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

					if (currentSpace == "Out of Lab" or newSpace == "Out of Lab"):
						continue
					if (currentSpace == newSpace):
						continue
					locationTuple = (currentSpace, newSpace)
					energyDiff = newEnergy - currentEnergy

					if (user not in IE): #instantiate individual events if needed
						IE[user] = {}
					if (locationTuple not in IE[user]):
						IE[user][locationTuple] = [energyDiff]
					else:
						IE[user][locationTuple].append(energyDiff)





					if (locationTuple not in TE): #instantiate total events if needed
						TE[locationTuple] = [energyDiff]
					else:
						TE[locationTuple].append(energyDiff)




					if (user not in ISP): #instantiate individual space preferences if needed
						ISP[user] = {}
					if (location not in ISP[user]):
						ISP[user][location] = 1
					else:
						ISP[user][location] += 1

	def getStatistics(self):
		for action in TE:
			print(action[0], end="")
			print(" to ", end="")
			print(action[1], end="")
			print(", total: ", end="")
			listSum = len(TE[action])
			print(listSum, end="")
			print(", average: ", end="")
			print(sum(TE[action])/float(listSum), end="")
			print(", median: ",)


M = moveSuggestionGenerator()
M.scrapeData()
M.getStatistics()













