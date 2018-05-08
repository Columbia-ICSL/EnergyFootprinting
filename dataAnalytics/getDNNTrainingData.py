import DBScrape
import datetime
import calendar
import sys
import time
from spaceNames import S
from personal import P
from IDs import peopleID
print "This is the name of the script: ", sys.argv[0]
print "Number of arguments: ", len(sys.argv)
if len(sys.argv) != 7:
	print "Supply arguments to this script. Example: python separateFootprint.py {beginYear} {beginMonth} {beginDay} {endYear} {endMonth} {endDay}"
	assert(len(sys.argv) == 7)


parameters = sys.argv[1:]
for i in range(len(parameters)):
	parameters[i] = int(parameters[i])



class getTrainingData:
	def __init__(self, spaces, personal, ids, startYear, startMonth, startDay, endYear, endMonth, endDay, verbose):
		self.multiplier = 0.3

		self.data = []
		self.databaseScrape = DBScrape.DBScrape()
		begin = datetime.datetime(startYear, startMonth, startDay)
		end = datetime.datetime(endYear, endMonth, endDay)
		begin = calendar.timegm(begin.utctimetuple())
		end = calendar.timegm(end.utctimetuple())
		self.footprints = {}
		self.personal = {}
		self.timestamps = []

		self.verbose = verbose
		self.spaces = spaces
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

		self.shots = self.databaseScrape.snapshots_col_appliances(begin, end)
		self.pShots = self.databaseScrape.snapshots_col_users(begin, end)
		# get number of location recs
		# get number of plugmeters
		# get number of rooms
		# get number of people
		self.offsetVec1 = len(self.peopleDef)
		self.offsetVec2 = self.offsetVec1 + len(self.spaceDef)
		self.offsetVec3 = self.offsetVec2 + len(self.deviceDef)
		self.vecLen = len(self.peopleDef) + len(self.spaceDef) + len(self.deviceDef)
		# length of input vector: occupants, reducible shared energy, personal energy, room occupancy

		self.offset1 = len(self.peopleDef) * len(self.spaceDef)
		self.offset2 = self.offset1 + len(self.deviceDef)
		self.offset3 = self.offset2 + len(self.spaceDef)
		self.offset4 = self.offset3 + len(self.peopleDef)
		self.recLen = self.offset4 # len of recommendation vector
		print("Done Init")

		


	def printC(self, text):
		if self.verbose:
			print text
	
	def getSnapshots(self):
		shots = self.shots
		self.printC("Found " + str(len(shots)) + " snapshots")
		i = 0
		for shot in shots:
			print(str(i*1.0/len(shots)) + " percent complete")
			timestamp = shot["timestamp"]
			pattern1 = '%Y-%m-%d %H:%M:%S.%f'
			pattern2 = '%Y-%m-%d %H:%M:%S'
			#self.printC(timestamp)
			try:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern1)))
			except ValueError:
				epoch = int(time.mktime(time.strptime(str(timestamp), pattern2)))

			self.timestamps.append(timestamp)
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
						print "room " + room + " not in space database"
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

	def recommendations(self):
		shots = self.pShots
		state0 = self.getState(shots[0])

		for i in range(1,len(shots)):
			print(str(i*1.0/len(shots)) + " percent done with recs")
			state1 = self.getState(shots[i])
			tempRecs = self.getRecommendations(state0, state1)
			state0[-1] = 72
			self.saveToFile(state0, tempRecs)
			state0 = state1

	def getRecommendations(self, state0, state1):
		index0 = state0[-1]
		index1 = state1[-1]
		recs = [0]*self.recLen
		for i in range(len(self.peopleDef)):

			if state0[i] != 0:
				for j in range(len(self.spaceDef)):
					loc0 = state0[i]
					loc1 = j
					#loc1 = state1[i]
					occupancy0old = state0[self.vecLen + loc0]
					occupancy1old = state0[self.vecLen + loc1]
					occupancy0new = state1[self.vecLen + loc0]
					occupancy1new = state1[self.vecLen + loc1]
					reward = 0
					if occupancy0new == 0:
						reward += self.footprints[self.spaceDefInv[loc0]][index0]
					if occupancy1old == 0:
						reward -= self.footprints[self.spaceDefInv[loc1]][index1]
					recs[i*len(self.spaceDef) + loc1] = reward
		for j in range(len(self.deviceDef)):
			deviceEnergy = state0[j+self.offsetVec1]
			if deviceEnergy > 100:
				recs[j+self.offset1] = deviceEnergy/2.0
		for k in range(len(self.spaceDef)):
			occupancy0 = state0[k+self.offsetVec2]
			if occupancy0 == 1:
				recs[k+self.offset2] = self.footprints[self.spaceDefInv[k]][index0]
		return recs

	def saveToFile(self, state, recs):
		with open("x.csv", "a") as trainingFile:
			trainingFile.write(state)
		with open("y.csv", "a") as labelFile:
			labelFile.write(recs)

GF = getTrainingData(S, P, peopleID, parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5], True)
GF.getSnapshots()
GF.recommendations()



