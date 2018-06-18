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
		self.multiplier = 1.0
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
		for feed in self.feedback:
			timestamp = feed["timestamp"]
			index = 0
			for t in range(len(self.timestamps)-1):
				if timestamp > self.timestamps[t] and timestamp <= self.timestamps[t+1]:
					index = t
					break
			state = self.getState(self.shots[index])
			newState = copy.copy(state)
			message = feed["messageID"]
			messageSplit = message.split("|")
			recType = messageSplit[0]
			device = messageSplit[1]
			extra = messageSplit[2]

			if (recType == "move"):
				print("Recommendation: " + device + " move to " + extra)
				personNum = self.peopleDef[device]
				spaceNum = self.spaceDef[extra]
				newState[personNum] = spaceNum
				energySaved = self.getSpaceCons(device, extra, t)
				print("Energy Saved: " + str(energySaved) + " Wh")
				
		
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

	def getSpaceCons(self, user, space, t):
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
				if user not in shot["data"]:
					startLoc = self.defaultSpace(user)
				else:
					startLoc = shot["data"][user]["location"]


				for ID in shot["data"]:
					if ID not in self.peopleDef:
						continue
					loc = shot["data"][ID]["location"]
					if loc == startLoc:
						occStart += 1
					if loc == space:
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
		if endTime - targetTimestamp < datetime.timedelta(hours=1):
			endTime = targetTimestamp + datetime.timedelta(hours=1)
		startTime = None
		for shot in shots:
			timestamp = shot["timestamp"]
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
			if space not in self.footprints:
				saved = 0
			else:
				saved = self.footprints[startLoc][t]
			lost = 0
			if startLoc not in self.footprints:
				lost = 0
			else:
				lost = self.footprints[space][t]
			if occStart < 1:
				saved = 0
			if occEnd >= 1:
				lost = 0
			energySaved += (saved - lost)*p
		return energySaved

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


peopleID = Jgroup + Bgroup + Tgroup
GF = newTrainingData(S, NS, P, peopleID, parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5], parameters[6], parameters[7], False)
GF.getSnapshots()
GF.generateData()
