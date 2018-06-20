import DBScrape
import datetime
import calendar
import sys
import time
import csv
import copy
import random
from spaceNames import S
from spaceNames import NS
from personal import P
from IDs import Jgroup
from IDs import Tgroup
from IDs import Bgroup
from appliances import A

#Glossary
#self.spaceDef: dictionary -> space name (e.g. nwc1008) -- space number (e.g. 3)
#self.spaceDefInv: inverse of self.spaceDef -> space number -- space name
#self.peopleDef: dictionary -> user ID (e.g. "8121dbb04774e368") -- person number (e.g. 1)
#self.deviceDef: dictionary -> device ID (e.g. "nwc1007_plug1") -- device number (e.g. 1)
#self.spaceDictionary: dictionary of default spaces -> user ID -- default space
#self.timestamps: list of timestamps
#self.footprints: dictionary -> 

print "This is the name of the script: ", sys.argv[0]
print "Number of arguments: ", len(sys.argv)
if len(sys.argv) != 9:
	print "Supply arguments to this script. Example: python separateFootprint.py {beginYear} {beginMonth} {beginDay} {endYear} {endMonth} {endDay}"
	assert(len(sys.argv) == 9)


parameters = sys.argv[1:]
for i in range(len(parameters)):
	parameters[i] = int(parameters[i])

class newTrainingData:
	def __init__(self, spaces, nonSpaces, personal, ids, startYear, startMonth, startDay, startHour, endYear, endMonth, endDay, endHour, verbose):
		self.multiplier = 0.2
		self.setDefault()
		self.data = []
		self.databaseScrape = DBScrape.DBScrape()
		begin = datetime.datetime(startYear, startMonth, startDay, startHour)
		end = datetime.datetime(endYear, endMonth, endDay, endHour)
		begin = calendar.timegm(begin.utctimetuple())
		end = calendar.timegm(end.utctimetuple())

		self.footprints = {}
		self.personal = {}
		self.timestamps = []
#		self.peopleLocations = {}

		self.banned = ["nwcM1_fcu", "nwcM2_fcu", "nwcM3_fcu", "nwcM4_fcu", "nwc1008_fcu"]
		self.verbose = verbose
		self.spaces = spaces + nonSpaces
		self.personalDevices = personal
		self.peopleID = ids

		print("Found " + str(len(self.spaces)) + " spaces")
		self.spaceDef = {}
		i = 0
		for room in self.spaces:
			if (i == 0):
				assert(room == "outOfLab") #first room must be out of lab
			self.footprints[room] = []
			self.spaceDef[room] = i
			i += 1

		self.spaceDefInv = {v: k for k, v in self.spaceDef.items()}

		self.peopleDef = {}
		i = 0
		for person in self.peopleID:
			self.peopleDef[person] = i
			i += 1

		self.deviceDef = {}
		i = 0
		for device in self.personalDevices:
			self.personal[device] = []
			self.deviceDef[device] = i
			i += 1

		self.feedback = self.databaseScrape.getFeedback(begin, end)
		self.shots = self.databaseScrape.snapshots_col_appliances(begin, end)
		self.pShots = self.databaseScrape.snapshots_col_users(begin, end)

		self.offsetVec1 = len(self.peopleDef)
		self.offsetVec2 = self.offsetVec1 + len(self.spaceDef)
		self.offsetVec3 = self.offsetVec2 + len(self.deviceDef)
		self.vecLen = len(self.peopleDef) + len(self.spaceDef) + len(self.deviceDef)
		self.inputLen = self.vecLen + len(self.spaceDef) + 1
		# length of input vector: occupants, reducible shared energy, personal energy, room occupancy

		self.offset1 = len(self.peopleDef) * len(self.spaceDef)
		self.offset2 = self.offset1 + len(self.deviceDef)
		self.offset3 = self.offset2 + len(self.spaceDef)
		self.offset4 = self.offset3 + len(self.peopleDef)
		self.recLen = self.offset4 # len of recommendation vector

	def printC(self, text):
		if self.verbose:
			print text

	def generateData(self):
		numRecs = 0
		energyRecs = 0.0
		pSum = 0.0
		pxSum = 0.0
		PnumRecs = 0
		PenergyRecs = 0.0
		PpSum = 0.0
		PpxSum = 0.0
		


		for feed in self.feedback:
			timestamp = feed["timestamp"]
			index = 0
			for t in range(len(self.timestamps)-1):
				if timestamp > self.timestamps[t] and timestamp <= self.timestamps[t+1]:
					index = t
					break

			state = self.getState(self.shots[index])
			newState = copy.copy(state)
			accepted = feed["accepted"]
			message = feed["messageID"]
			messageSplit = message.split("|")
			recType = messageSplit[0]
			device = messageSplit[1]
			extra = messageSplit[2]
			if device not in self.peopleDef:
				continue
			
			if (recType == "move"):
				print("Recommendation: " + device + " move to " + extra)
				personNum = self.peopleDef[device]
				spaceNum = self.spaceDef[extra]
				newState[personNum] = spaceNum
				if accepted:
					(energySaved, p, pX) = self.getSpaceCons(device, extra, t, 5)
					if energySaved < 0:
						continue
					energyRecs += energySaved
					pSum += p
					pxSum += pX
					numRecs += 1
				else:
					(energySaved, p, pX) = self.getSpaceCons(device, extra, t, 5)
					PenergyRecs += energySaved
					if energySaved < 0:
						continue
					PpSum += p
					PpxSum += pX
					PnumRecs += 1
				print("Energy Saved: " + str(energySaved) + " Wh")
		if (numRecs > 0):
			print("Average Energy Saved: " + str(energyRecs/float(numRecs)) + " Wh")
			print("Number of Recommendations: " + str(numRecs))
			print("Average Rec Duration: " + str(pSum/float(numRecs)*60.0) + " minutes" + ", EX: " + str(pxSum/float(numRecs)))
			print("Total Energy Saved: " + str(energyRecs) + " Wh")
			print("\n")
		if (PnumRecs > 0):
			print("Potential Average Energy Saved: " + str(PenergyRecs/float(PnumRecs)) + " Wh")
			print("Number of Recommendations: " + str(PnumRecs))
			print("Average Rec Duration: " + str(PpSum/float(PnumRecs)*60.0) + " minutes" + ", EX: " + str(PpxSum/float(PnumRecs)))
			print("Potential Total Energy Saved: " + str(PenergyRecs) + " Wh")

		#self.getSchedules()
		self.getBaseline()
			
	def defaultSpace(self, user):
		spaceName = self.spaceDictionary[user]
		return spaceName#self.spaceDef[spaceName]

	def setDefault(self):
		self.spaceDictionary = {} #dictionary of default spaces -> user ID -- default space
		self.spaceDictionary["8121dbb04774e368"] = "nwc1008"
		self.spaceDictionary["2e2848888facd607"] = "nwc1003b_c"
		self.spaceDictionary["FD0C2D0E-C244-486E-8518-D1D8F3C52894"] = "nwc1003b_b"
		self.spaceDictionary["A2193EE3-EFDC-4F9B-8793-3AB25EBC6BA3"] = "nwc1003b_a"

		self.spaceDictionary["313925b2df2f6066"] = "nwc1000m_a1"
		self.spaceDictionary["36cd923d8be79f40"] = "nwc1000m_a2"
		self.spaceDictionary["C73BD956-BCE1-46FD-A40D-0BD9F0B2DE24"] = "nwc1000m_a2"

		self.spaceDictionary["F6D75545-6454-4290-BA6F-E96461FF84CA"] = "nwc1000m_a5"
		self.spaceDictionary["3E71DA71-28F4-4043-B482-FBDCBF321584"] = "nwc1000m_a5"

	def prioritySpace(self, user):
		icslSpace = [0,5,7,8,9,13,14,15,16]
		bSpace = [0,1,11,12]
		tSpace = [0,6,10,14]
		if user in Jgroup:
			index = random.randint(0, len(icslSpace)-1)
			return icslSpace[index]
		if user in Bgroup:
			index = random.randint(0, len(bSpace)-1)
			return bSpace[index]
		if user in tSpace:
			index = random.randint(0, len(tSpace)-1)
			return tSpace[index]
		return 0

	def occupancySimul(self):
		timeDictionary = {}
		Peter = []
		Kevin = []
		Stephen = []
		LeiLei = []
		randomPeople = []
		for day in range(21, 32):
			startTime = datetime.datetime(2018, 5, day, 11, 0, 0)
			endTime = datetime.datetime(2018, 5, day, 19, 0, 0)
			Peter.append((startTime,endTime))
			startTime = datetime.datetime(2018, 5, day, 11, 0, 0)
			endTime = datetime.datetime(2018, 5, day, 19, 0, 0)
			Kevin.append((startTime,endTime))
			startTime = datetime.datetime(2018, 5, day, 8, 0, 0)
			endTime = datetime.datetime(2018, 5, day, 18, 0, 0)
			Stephen.append((startTime,endTime))
			startTime = datetime.datetime(2018, 5, day, 12, 0, 0)
			endTime = datetime.datetime(2018, 5, day, 16, 0, 0)
			LeiLei.append((startTime,endTime))
			startTime = datetime.datetime(2018, 5, day, 10, 0, 0)
			endTime = datetime.datetime(2018, 5, day, 16, 0, 0)
			randomPeople.append((startTime, endTime))
		for day in range(1, 20):
			startTime = datetime.datetime(2018, 6, day, 11, 0, 0)
			endTime = datetime.datetime(2018, 6, day, 19, 0, 0)
			Peter.append((startTime,endTime))
			startTime = datetime.datetime(2018, 6, day, 11, 0, 0)
			endTime = datetime.datetime(2018, 6, day, 19, 0, 0)
			Kevin.append((startTime,endTime))
			startTime = datetime.datetime(2018, 6, day, 8, 0, 0)
			endTime = datetime.datetime(2018, 6, day, 18, 0, 0)
			Stephen.append((startTime,endTime))
			startTime = datetime.datetime(2018, 6, day, 12, 0, 0)
			endTime = datetime.datetime(2018, 6, day, 16, 0, 0)
			LeiLei.append((startTime,endTime))
			startTime = datetime.datetime(2018, 6, day, 10, 0, 0)
			endTime = datetime.datetime(2018, 6, day, 16, 0, 0)
			randomPeople.append((startTime, endTime))
		timeDictionary["nwc1003b_a"] = Peter
		timeDictionary["nwc1003b_b"] = Kevin
		timeDictionary["nwc1003b_c"] = Stephen
		timeDictionary["nwc1003b_danino"] = LeiLei
		timeDictionary["nwc1003b_t"] = randomPeople
		return timeDictionary

	def getBaseline(self):
		shots = self.shots
		passiveEnergySaved = 0.0
		optimalEnergySaved = 0.0
		totalEnergy = 0.0
		powerCurve = self.getEnergy()
		oldTime = self.timestamps[0]
		timeDictionary = self.occupancySimul()
		for t in range(len(self.timestamps)):
			timestamp = self.timestamps[t]

			if timestamp.hour < 8 or timestamp.hour >= 20:
				oldTime = timestamp
				continue
			timeDiff = timestamp - oldTime
			pHour = datetime.timedelta(hours=1)
			pHour = pHour.total_seconds()
			timefrac = timeDiff.total_seconds()/pHour
			for room in self.footprints:
				noSave = False

				cons = self.footprints[room][t]
				if room in timeDictionary:
					times = timeDictionary[room]
					for time in times:
						if timestamp > time[0] and timestamp < time[1]:
							noSave = True
							break

				if noSave == False:
					passiveEnergySaved += cons * timefrac
				optimalEnergySaved += cons * timefrac
			totalEnergy += powerCurve[t] * timefrac
			oldTime = timestamp
		print("Passive Energy Saved: " + str(passiveEnergySaved) + " Wh")
		print("Optimal Energy Saved: " + str(optimalEnergySaved) + " Wh")
		print("Total Energy Consumption: " + str(totalEnergy) + " Wh")



	def getSchedules(self):
		shots = self.pShots
		scheduleTimes = {}

		startDate = shots[1]["timestamp"]
		newStartDate = datetime.datetime(startDate.year, startDate.month, startDate.day)
		newEndDate = newStartDate + datetime.timedelta(days=1)

		for user in self.peopleDef:
			scheduleTimes[user] = [(None, None)]


		print(newStartDate)
		print(newEndDate)

		for shot in shots:
			timestamp = shot["timestamp"]
			if timestamp > newEndDate:
				newStartDate = newEndDate
				newEndDate = newEndDate + datetime.timedelta(days=1)
				for user in scheduleTimes:
					scheduleTimes[user].append((None, None))
			if user in shot["data"]:
				(l1, l2) = scheduleTimes[user][-1]
				if l1 is None:
					scheduleTimes[user][-1] = (timestamp, timestamp)
				else:
					scheduleTimes[user][-1] = (l1, timestamp)

		for user in scheduleTimes:
			print("Schedule for User: " + user)
			for times in scheduleTimes[user]:
				st0 = times[0]
				st1 = times[1]
				print(st0)
				print(st1)




	def getSpaceCons(self, user, space, t, limit):
		space1 = space
		if (space1 == "nwc1003b_danino"):
			space1 = "nwc1000m_a2"
		shots = self.pShots
		targetTimestamp = self.timestamps[t]
		energySaved = 0.0
		startLoc = None
		endTime = None
		occStart = 0
		occEnd = 0
		for shot in shots:
			timestamp = shot["timestamp"]
			if timestamp <= targetTimestamp:
				continue
			if startLoc is None:
				if "data" not in shot:
					continue
				if user not in shot["data"] or shot["data"][user]["location"] == "outOfLab":
					startLoc = self.defaultSpace(user)
				else:
					startLoc = shot["data"][user]["location"]


				for ID in shot["data"]:
					if ID not in self.peopleDef:
						continue
					loc = shot["data"][ID]["location"]
					if loc == startLoc:
						occStart += 1
					if loc == space1:
						occEnd += 1


			else:
				if "data" not in shot:
					continue
				if user not in shot["data"]:
					newLoc = "OutOfLab"
				else:
					newLoc = shot["data"][ID]["location"]
				if newLoc == startLoc:
					continue
				else:
					endTime = timestamp
					break
		shots = self.shots
		recTimeExperiment = endTime-targetTimestamp
		pHour = datetime.timedelta(hours=1)
		pHour = pHour.total_seconds()
		recTimeExperiment = recTimeExperiment.total_seconds()/pHour
		if endTime - targetTimestamp < datetime.timedelta(hours=limit):
			endTime = targetTimestamp + datetime.timedelta(hours=limit)
		startTime = None
		print("Start Location: " + startLoc + ", End Location: " + space1)
		print("Start Energy: " + str(self.footprints[startLoc][t]) + ", End Energy: " + str(self.footprints[space1][t]))
		print("Start Occupancy: " + str(occStart) + ", End Occupancy: " + str(occEnd))

		recTime = endTime-targetTimestamp
		pHour = datetime.timedelta(hours=1)
		pHour = pHour.total_seconds()
		recTime = recTime.total_seconds()/pHour
		#for shot in shots:
		for t1 in range(len(self.timestamps)):
			#timestamp = shot["timestamp"]
			timestamp = self.timestamps[t1]
			if timestamp <= targetTimestamp:
				continue
			if timestamp > endTime:
				break
			if startTime is None:
				startTime = timestamp
				continue
			p = timestamp - startTime
			startTime = timestamp
			p1 = p.total_seconds()
			p2 = datetime.timedelta(hours=1)
			p2 = p2.total_seconds()
			p = p1/p2
			saved = 0
			if space1 not in self.footprints:
				saved = 0
			else:
				saved = self.footprints[startLoc][t1]
			lost = 0
			if startLoc not in self.footprints:
				lost = 0
			else:
				lost = self.footprints[space1][t1]
			if occStart > 1:
				saved = 0
			if occEnd >= 1:
				lost = 0
			energySaved += (saved - lost)*p

		return (energySaved, recTime, recTimeExperiment)

	def getEnergy(self):
		shots = self.shots
		powerCurve = []
		#powers = {}
		#for applianceName in shots[0]["data"]:
		#	powers[applianceName] = []
		for shot in shots:
			powerCurve.append(0.0)
#			for applianceName in A:
#				powers[applianceName].append(0.0)
			for applianceName in shot["data"]:
				if applianceName in self.banned:
					continue
				appliance = shot["data"][applianceName]
				powerCurve[-1] += appliance["value"]
		#		powers[applianceName][-1] = appliance["value"]
		#for applianceName in powers:
		#	s = 0.0
		#	for i in range(len(powers[applianceName])):
		#		s += powers[applianceName][i]
		#	print("Appliance " + applianceName + str(s/len(powers[applianceName])))
		return powerCurve
				

	def getSnapshots(self):
		shots = self.shots
		self.printC("Found " + str(len(shots)) + " snapshots")
		i = 0
		for shot in shots:
			self.printC(str(i*1.0/len(shots)) + " percent complete")
			timestamp = shot["timestamp"]
			pattern1 = '%Y-%m-%d %H:%M:%S.%f'
			pattern2 = '%Y-%m-%d %H:%M:%S'
			#self.printC(timestamp)
			try:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern1)))
			except ValueError:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern2)))

			self.timestamps.append(timestamp)
#			for user in self.peopleDef:
#				self.peopleLocations[user].append(0)
			for room in self.spaces:
				self.footprints[room].append(0)
			for p in self.personal:
				self.personal[p].append(0)
			
			for applianceName in shot["data"]:
				if applianceName in self.banned:
					continue
				appliance = shot["data"][applianceName]
				rooms = appliance["rooms"]
				t = appliance["type"]
				if t == "Electrical":
					if applianceName in self.personal:
						self.personal[applianceName][-1] = appliance["value"]
					continue
				numRooms = len(rooms)
				for room in rooms:
					if room not in self.footprints:
						self.printC("room " + room + " not in space database")
						continue
					if t == "HVAC":
						self.footprints[room][-1] = self.footprints[room][-1] + appliance["value"]*self.multiplier/numRooms
					elif t == "Light":
						self.footprints[room][-1] = self.footprints[room][-1] + appliance["value"]/numRooms
			i += 1
		print("\n\n\nDone getting snapshots\n\n\n")

	def getState(self, shot):
		state = [0] * self.vecLen

		timestamp = shot["timestamp"]
		pattern1 = '%Y-%m-%d %H:%M:%S.%f'
		pattern2 = '%Y-%m-%d %H:%M:%S'
		try:
			epoch = int(time.mktime(time.strptime(str(timestamp), pattern1)))
		except ValueError:
			epoch = int(time.mktime(time.strptime(str(timestamp), pattern2)))

		locations = [0] * len(self.spaceDef) #array of number of people in each space
		for ID in shot["data"]:
			if ID not in self.peopleDef:
				continue
			IDnum = self.peopleDef[ID] #person number
			loc = shot["data"][ID]["location"]
#			if loc == "outOfLab":
#				loc = self.defaultSpace(ID)

			locnum = self.spaceDef[loc] #location number
			locations[locnum] += 1
			state[IDnum] = locnum #assign space to input vector

		index = 0
		for t in range(len(self.timestamps)-1):
			if timestamp > self.timestamps[t] and timestamp <= self.timestamps[t+1]:
				index = t
				break
		for room in self.footprints:
			energy = self.footprints[room][index]
			roomIndex = self.spaceDef[room]
			offset = len(self.peopleDef)
			state[roomIndex + offset] = energy
		for device in self.personal:
			energy = self.personal[device][index]
			deviceIndex = self.deviceDef[device]
			offset = len(self.peopleDef) + len(self.spaceDef)
			state[deviceIndex + offset] = energy
		state += locations
		state.append(index) #just to keep the time
		return state

	def getMoveNextState(self, state0, startSpace, endSpace):
		nextStates = []
		stateSamples = 100
		for sample in range(len(stateSamples)):
			newNextState = copy.copy(state0)
			for i in range(len(self.peopleDef)):
				for j in range(len(self.spaceDef)):
					newNextState = copy.copy(state0)
					newNextState[i] = j
					nextStates.append(newNextState)

		for i in range(len(self.spaceDef)):
			newNextState = copy.copy(state0)
			newNextState[self.offsetVec1 + i] -= tempRecs[self.offset2 + i]
			nextStates.append(newNextState)
		return nextStates


	def saveToFile(self, state, recs, nextStates):
		with open("x.csv", "a") as trainingFile:
			for i in range(len(nextStates)):
				wr = csv.writer(trainingFile,delimiter=',')
				wr.writerow(state)
		with open("y.csv", "a") as labelFile:
			for i in range(len(nextStates)):
				wr = csv.writer(labelFile,delimiter=',')
				wr.writerow([recs[i]])
		with open("z.csv", "a") as nextFile:
			for i in range(len(nextStates)):
				nextStates[i][-1] = 72
				wr = csv.writer(nextFile,delimiter=',')
				wr.writerow(nextStates[i])


peopleID = Jgroup + Bgroup + Tgroup
GF = newTrainingData(S, NS, P, peopleID, parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5], parameters[6], parameters[7], False)
GF.getSnapshots()
GF.generateData()
