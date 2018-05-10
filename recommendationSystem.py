import cloudserver
from threading import Thread
import time
import datetime
import numpy as np
import cvxopt
from cvxopt import glpk
import random
from spaceNames import S
from spaceNames import NS
from personal import P
from IDs import Jgroup
from IDs import Tgroup
from IDs import Bgroup

class recommenderSystem:
	def __init__(self):
		self.initState()
		self.setup()
		self.startDaemon()

	def initState(self):
		self.footprints = {}
		self.personal = {}
		self.spaceDef = {}
		self.spaces = S
		print("Found " + str(len(self.spaces)) + " spaces")
		self.personalDevices = P
		self.peopleID = Jgroup+Bgroup+Tgroup
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
		self.offsetVec1 = len(self.peopleDef)
		self.offsetVec2 = self.offsetVec1 + len(self.spaceDef)
		self.offsetVec3 = self.offsetVec2 + len(self.deviceDef)
		self.vecLen = len(self.peopleDef) + len(self.spaceDef) + len(self.deviceDef)
		
		self.offset1 = len(self.peopleDef) * len(self.spaceDef)
		self.offset2 = self.offset1 + len(self.deviceDef)
		self.offset3 = self.offset2 + len(self.spaceDef)
		self.offset4 = self.offset3 + len(self.peopleDef)
		self.recLen = self.offset4 # len of recommendation vector


	def setup(self):
		self.checkInterval = 10
		self.users = None
		self.userRecommendations = {}
		self.locations = {}
		self.rewards = {}
		self.HVAC = {}
		self.Lights = {}
		self.Electric = {}
		self.SpaceParameters = {}
		self.spaces = {}
		self.spaceNames = []
		self.a = [] #room HVAC variance
		self.b = [] #room light variance
		self.z = [] #room max occupancy
		self.x = 0 #current occupancy
		self.getUsers()
		self.setSpaceParameters()

		#self.getUserLocations()
	
	def setSpaceParameters(self, temp=72):
		rooms = cloudserver.db.list_of_rooms
		self.spaces = rooms
		for room in rooms:
			print("Loading room " + str(room) + "...")
			self.SpaceParameters[room] = 0.2

	def getUsers(self):
		#create a list of users from the database
		self.users = cloudserver.db.dumpUsers()
		print "Loaded " + str(len(self.users)) + " users"
		for user in self.users:
			if "name" not in user or "userID" not in user:
				continue
			self.userRecommendations[user["userID"]] = []
			self.rewards[user["userID"]] = user["balance"]
		print "Loaded user recommendations dictionary"

	def loadBuildingParams(self):
		appliances = cloudserver.db.list_of_appliances
		self.HVAC = {}
		self.Lights = {}
		self.Electric = {}
		rooms = cloudserver.db.list_of_rooms
		for room in rooms:
			self.HVAC[room] = 0
			self.Lights[room] = 0
			self.Electric[room] = 0
		print("Loading building parameters...")
		for app in appliances:
			appliance = appliances[app]
			rooms = appliance["rooms"]
			value = appliance["value"]
			t = appliance["type"]
			n = len(rooms)
			for room in rooms:
				if t == "Electrical":
					if room not in self.Electric:
						self.Electric[room] = value/n
					else:
						self.Electric[room] += value/n
				elif t == "Light":
					if room not in self.Lights:
						self.Lights[room] = value/n
					else:
						self.Lights[room] += value/n
				elif t == "HVAC":
					if room not in self.HVAC:
						self.HVAC[room] = value/n
					else:
						self.HVAC[room] += value/n
		print("Finished loading building parameters.")

	def getUserLocations(self):
		self.locations = cloudserver.db.location_of_users
		return

	def returnRecs(self, user):
		balance = 0
		if user in self.rewards:
			balance = self.rewards[user]
		tempBalance = balance
		json_return={
            "location":"Location Name",
            "location_id":"locationIDString",
            "balance":balance,
            "tempBalance": tempBalance,
            "suggestions":[]
		}
		location = "outOfLab"
		if user in self.locations:
			location = self.locations[user]
		json_return["location_id"]=location
		json_return["location"]=cloudserver.db.RoomIdToName(location)
		if user in self.userRecommendations:	
			for rec in self.userRecommendations[user]:
				json_return["suggestions"].append(rec)
		ret = cloudserver.db._encode(json_return,False)
		return ret

	def bestRecommendations(self, solutions):
		for user in self.userRecommendations:
			self.userRecommendations[user] = []
		#print("Getting best recommendations....")
		#print(solutions)
		for user in self.locations:
			if user not in self.userRecommendations:
				continue
			#print(self.locations[user])
			if (self.locations[user]) not in solutions:
				r = random.choice(list(solutions))
				suggestion = self.make_suggestion_item("move", "Move to " + r, "Move recommendation from " + self.locations[user] + " to " + r, 100, "Hello World", 1)
				self.userRecommendations[user].append(suggestion)
		return

	def make_suggestion_item(self, iType, iTitle, iBodyText, iReward, messageID, inotification=0, Others={}):
		Others.update({
            "type":iType,
            "title":iTitle,
            "body":iBodyText,
            "reward":iReward,
            "notification":inotification,
            "messageID":messageID
            })
		return Others

	def LPOptimization(self, spaces, a, b, z, x1):
		energySum = []
		solutions = {}
		assert(len(a) == len(b))
		for i in range(len(a)):
			energySum.append(a[i] + b[i])

		c = cvxopt.matrix(energySum, tc='d')
		G = cvxopt.matrix(z, tc='d')
		h = cvxopt.matrix([-1*x1], tc='d')
		(status, x) = cvxopt.glpk.ilp(c,G.T,h,I=set(range(len(a))),B=set(range(len(a))))
		print(status)
		print(x)
		for i in range(len(a)):
			if x[i] > 0.5:
				solutions[spaces[i]]= -1*z[i]
		return solutions

	def formatInputs(self):
		self.spaceNames = []
		self.a = [] #room HVAC variance
		self.b = [] #room light variance
		self.z = [] #room max occupancy
		self.x = 0 #current occupancy
		for s in self.spaces:
			space = self.spaces[s]
			if space["space"] == 1 and space["lab"] == 3:
				self.spaceNames.append(s)
				self.z.append(-1*space["maxOccupancy"])
				HVAC = self.HVAC[s]*self.SpaceParameters[s]
				self.a.append(HVAC)
				Light = self.Lights[s]
				self.b.append(Light)
		self.x = len(self.locations)


	def getSnapshot(self):
		shot = cloudserver.db.snapshots_col_appliances.find().skip(cloudserver.db.snapshots_col_appliances.count()-1)
		shot = list(shot)
		shot = shot[0]
		for room in self.spaces:
			self.footprints[room] = 0 # shared energy (HVAC + Lights)
		for p in self.personal:
			self.personal[p] = 0 # personal energy (plugmeters)
		for applianceName in shot["data"]:
			appliance = shot["data"][applianceName]
			rooms = appliance["rooms"]
			t = appliance["type"]
			if t == "Electrical":
				if applianceName in self.personal:
					self.personal[applianceName] = appliance["value"]
				continue
			numRooms = len(rooms)
			for room in rooms:
				if room not in self.footprints:
					print "room " + room + " not in space database"
					continue
				if t == "HVAC":
					self.footprints[room] += self.footprints[room] + appliance["value"]/numRooms#*self.multiplier/numRooms
				elif t == "Light":
					self.footprints[room] += self.footprints[room] + appliance["value"]/numRooms

	def getState(self):
		self.getSnapshot()
		state = [0] * self.vecLen
		shot = cloudserver.db.snapshots_col_users.find().skip(cloudserver.db.snapshots_col_users.count()-1)
		locations = [0] * len(self.spaceDef) #array of number of people in each space
		for ID in shot["data"]:
			if ID not in self.peopleDef:
				continue
			IDnum = self.peopleDef[ID] #person number
			loc = shot["data"][ID]["location"]
			locnum = self.spaceDef[loc] #location number
			locations[locnum] += 1
			state[IDnum] = locnum #assign space to input vector

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
		state.append(72) #just to keep the time
		return state

	def deepLearning(self):
		state = self.getState()
		#import the neural network






	def runOptimization(self):
		self.setSpaceParameters()
		self.formatInputs()
		solutions = self.LPOptimization(self.spaceNames, self.a, self.b, self.z, self.x)
		self.bestRecommendations(solutions)


	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			self.getUserLocations()
			self.loadBuildingParams()


			self.deepLearning()
			self.runOptimization()
			print "Interval"
