import cloudserver
from threading import Thread
import time
import datetime
import numpy as np
import cvxopt
from cvxopt import glpk


class recommenderSystem:
	def __init__(self):
		self.setup()
		self.startDaemon()

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

	def bestRecommendations(self):

		return

	def make_suggestion_item(iType, iTitle, iBodyText, iReward, messageID, inotification=0, Others={}):
		Others.update({
            "type":iType,
            "title":iTitle,
            "body":iBodyText,
            "reward":iReward,
            "notification":inotification,
            "messageID":messageID
            })
		return Others

	def LPOptimization(self, spaces, a, b, z, x):
		energySum = []
		assert(len(a) == len(b))
		for i in range(len(a)):
			energySum.append(a[i] + b[i])

		c = cvxopt.matrix(energySum, tc='d')
		G = cvxopt.matrix(z, tc='d')
		h = cvxopt.matrix([x], tc='d')
		(status, x) = cvxopt.glpk.ilp(c,G.T,h,I=set(range(len(a))),B=set(range(len(a))))
		print(status)
		for i in range(len(a)):
			if x[i] > 0.5:
				print(spaces[i])

	def formatInputs(self):
		self.spaceNames = []
		self.a = [] #room HVAC variance
		self.b = [] #room light variance
		self.z = [] #room max occupancy
		self.x = 0 #current occupancy
		for s in self.spaces:
			space = self.spaces[s]
			if space["space"] == 1:
				self.spaceNames.append(s)
				self.z.append(space["maxOccupancy"])
				HVAC = self.HVAC[s]*self.SpaceParameters[s]
				self.a.append(HVAC)
				Light = self.Lights[s]
				self.b.append(Light)
		self.x = len(self.locations)




	def runOptimization(self):
		self.setSpaceParameters()
		self.formatInputs()
		self.LPOptimization(self.spaceNames, self.a, self.b, self.z, self.x)



	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			self.getUserLocations()
			self.loadBuildingParams()
			self.runOptimization()
			print "Interval"
