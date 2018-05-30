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
from spaceNames import realS
from personal import P
from IDs import Jgroup
from IDs import Tgroup
from IDs import Bgroup
import numpy as np
import tensorflow as tensf
import math

class recommenderSystem:
	def __init__(self):
		self.initState()
		self.setup()
		self.startDaemon()

	def initState(self):
		self.footprints = {}
		self.personal = {}
		self.spaceDef = {}
		self.nonSpaceDef = {}
		self.realSDef = {}
		self.spaces = S
		self.nonSpaces = NS
		self.realS = realS
		self.timeout = {}

		print("Found " + str(len(self.spaces)) + " spaces")
		self.personalDevices = P
		self.peopleID = Jgroup+Bgroup+Tgroup
		i = 0
		for room in self.spaces:
			if (i == 0):
				assert(room == "outOfLab") #first room must be out of lab
			self.footprints[room] = []
			self.spaceDef[room] = i
			self.realSDef[room] = self.realS[i]
			i += 1
		self.spaceDefInv = {v: k for k, v in self.spaceDef.items()}

		for room in self.nonSpaces:
			self.nonSpaceDef[room] = i
			i += 1
		self.nonSpaceDefInv = {v: k for k, v in self.nonSpaceDef.items()}

		self.peopleDef = {}
		i = 0
		for person in self.peopleID:
			self.timeout[person] = 0
			self.peopleDef[person] = i
			i += 1
		self.peopleDefInv = {v: k for k, v in self.peopleDef.items()}

		self.deviceDef = {}
		i = 0
		for device in self.personalDevices:
			self.personal[device] = []
			self.deviceDef[device] = i
			i += 1
		self.deviceDefInv = {v: k for k, v in self.deviceDef.items()}

		self.deviceOwnership = {}
		for device in self.personalDevices:
			self.deviceOwnership[device] = "Peter"
		
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
		self.checkInterval = 60*15 # 15 minutes
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
				print(rec)
		ret = cloudserver.db._encode(json_return,False)
		return ret

	def decideNotification(self, deviceID):
		if time.time() > self.timeout[deviceID] + 60*15:
			self.timeout[deviceID] = time.time()

	def clearRecommendations(self):
		for user in self.userRecommendations:
			self.userRecommendations[user] = []

	def bestRecommendations(self, solutions):

		#print("Getting best recommendations....")
		#print(solutions)
		for user in self.locations:
			if user not in self.userRecommendations:
				continue
			#print(self.locations[user])
			if (self.locations[user]) not in solutions:
				r = random.choice(list(solutions))
				message = "{0}|{1}|{2}".format("move", user, r)
				suggestion = self.make_suggestion_item("move", "Move", "Move to " + self.realSDef[r], 3, message, 0)
				self.checkRecommendation(user, suggestion)
		return

	def make_suggestion_item(self, iType, iTitle, iBodyText, iReward, messageID, inotification=0, Others={}):
		Others = {
            "type":iType,
            "title":iTitle,
            "body":iBodyText,
            "reward":iReward,
            "notification":inotification,
            "messageID":messageID
            }
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
		print("finished getting appliance data")

	def getState(self):
		self.getSnapshot()
		state = [0] * self.vecLen
		shot = cloudserver.db.snapshots_col_users.find().skip(cloudserver.db.snapshots_col_users.count()-1)
		shot = list(shot)
		shot = shot[0]
		locations = [0] * len(self.spaceDef) #array of number of people in each space
		for ID in shot["data"]:
			if ID not in self.peopleDef:
				continue
			IDnum = self.peopleDef[ID] #person number
			loc = shot["data"][ID]["location"]
			locnum = 0
			if loc in self.spaceDef:
				locnum = self.spaceDef[loc] #location number
			elif loc in self.nonSpaceDef:
				locnum = self.nonSpaceDef[loc]
			locations[locnum] += 1
			state[IDnum] = locnum #assign space to input vector

		for room in self.footprints:
			if room not in self.spaceDef:
				continue
			energy = self.footprints[room]

			roomIndex = self.spaceDef[room]
			offset = len(self.peopleDef)
			state[roomIndex + offset] = energy
		for device in self.personal:
			if device not in self.deviceDef:
				continue
			energy = self.personal[device]
			deviceIndex = self.deviceDef[device]
			offset = len(self.peopleDef) + len(self.spaceDef)
			state[deviceIndex + offset] = energy
		state += locations
		state.append(72) #just to keep the time
		print("Finished getting state")
		return state

	def randomRecommendations(self):
#		for user in self.locations:
		for user in self.userRecommendations:
#			if user not in self.userRecommendations:
#				continue
			#print(self.locations[user])
			r = random.choice(list(self.spaceDef.keys()))
			message = "{0}|{1}|{2}".format("move", user, r)
			body = "Move to " + self.realSDef[r] + "."
			rec = self.make_suggestion_item("move", "Move", body, 3, message, 0)
			self.checkRecommendation(user, rec)
#			self.userRecommendations[user].append(rec)
		for user in self.userRecommendations:
			message = "{0}|{1}|{2}".format("shift", user, "XXXX")
			body = "Come to lab now to save energy."
			rec = self.make_suggestion_item("shift", "Shift", body, 3, message, 0)
			self.checkRecommendation(user, rec)
#			self.userRecommendations[user].append(rec)
		for user in self.userRecommendations:
			message = "{0}|{1}|{2}".format("shade", user, "XXXX")
			body = "Lower shade on your window to save energy."
			rec = self.make_suggestion_item("shade", "Shade", body, 1, message, 0)
			self.checkRecommendation(user, rec)
#			self.userRecommendations[user].append(rec)
		return

	def deepLearning(self):
		state = self.getState()
		sess1 = tensf.Session()
		saver = tensf.train.import_meta_graph('./model_5_11/model_5_11.meta', clear_devices=True)
		saver.restore(sess1, tensf.train.latest_checkpoint('./model_5_11'))

		graph = tensf.get_default_graph()
		x1 = graph.get_tensor_by_name('s:0')
		y1 = graph.get_tensor_by_name('eval_net/l3/output:0')

		npState = np.array([state])

		with tensf.Session() as sess:
			sess.run(tensf.global_variables_initializer())
			y_out = sess.run(y1, feed_dict = {x1:npState})
			print("y_out length")
			print(str(y_out.shape))
		y_new = y_out.flatten()

		icslSpace = [0, 1, 5, 7, 8, 9, 13, 14, 15, 16]
		bSpace = [0, 1, 11, 12, 13, 14, 15, 16]
		tSpace  [0, 1, 6, 10, 13, 14, 15, 16]

		for user in self.peopleDef:
			personNum = self.peopleDef[user] #person number
			print(personNum)
			
			################
			## Kevin Chen 
			## Contextual Post filtering 
			###############

			###############
			## Intepret the group number to do filtering
			groupNum = 0
			if personNum < 3:
				groupNum = 1
			elif personNum < 6:
				groupNum = 2
			else:
				groupNum = 3
			###############
			## 10 percent exploring (delivering which ever has the largest reward)
			## 90 percent exploiting (do filtering to give more reasonable recommendation)
			token = random.Random()
			personalNum = np.argmax(y_new[self.offset1:self.offset2])
			if token < 0.9:
				print("Exploiting")
				#personActionNum = np.argmax(y_new[personNum*len(self.spaceDef):(personNum+1)*len(self.spaceDef)])
				if group == 1: ## icsl lab
					if personNum == 0: ## Fred, presumably only will work in his office
						print("Fred")
						personActionNum = 2
						
						## Add checking whether Fred's device has a positive reward		
					else: ## Kevin and Stephen, can work at any place available, other than professor's office
						print("Kevin and Stephen")
						personActionNum = np.argmax(y_new[personNum*len(self.spaceDef)+icslSpace])
				elif group == 2: ## Burke lab, can work at any place available, other than professor's office
					print("Burke Lab")
					personActionNum = np.argmax(y_new[personNum*len(self.spaceDef)+bSpace])
				else: #Teherani lab
					print("Teherani lab")
					personActionNum = np.argmax(y_new[personNum*len(self.spaceDef)+tSpace])
	
			else: 
				print("Exploring")
				personActionNum = np.argmax(y_new[personNum*len(self.spaceDef):(personNum+1)*(self.spaceDef)])
			
			rec1 = self.interpretAction(personActionNum, y_new[personActionNum])
			rec2 = self.interppretAction(personalNum, y_new[personalNum])
			if rec1 is not None:
				print("Got recommendation")
				self.checkRecommendation(user, rec1)
			else:
				print("Recommendation is not found")

			if rec2 is not None:
				print("Got recommendation")
				self.checkRecommendation(user, rec2)
			else:
				print("Recommendation is not found")



	def interpretAction(self, actionNum, reward):
		sign = 1
		if (reward < 0):
			sign = -1

		reward = math.log10(reward*sign)
		reward = reward * sign
		reward = int(reward)
		body = ""
		rec = None
		if actionNum < self.offset1:
			person = actionNum / len(self.spaceDef)
			space = actionNum % len(self.spaceDef)
			personName = self.peopleDefInv[person]
			spaceName = self.spaceDefInv[space]
			message = "{0}|{1}|{2}".format("move", personName, spaceName)
			body = "Move to " + self.realSDef[spaceName] + "."
			rec = self.make_suggestion_item("move", "Move", body, reward, message, 0)
		if actionNum >= self.offset1 and actionNum < self.offset2:
			device = actionNum - self.offset1
			deviceName = self.deviceDefInv[device]
			deviceOwner = self.deviceOwnership[deviceName]
			message = "{0}|{1}|{2}".format("reduce", deviceOwner, deviceName)
			body = "Reduce Power of " + deviceName
			rec = self.make_suggestion_item("reduce", "Reduce", body, reward, message, 0)
		if actionNum >= self.offset2 and actionNum:
			space = actionNum - self.offset2
			spaceName = self.spaceDefInv[space]
			message = "{0}|{1}|{2}".format("force", "BuildingManager", spaceName)
			body = "Force People from " + self.realSDef[spaceName]
			rec = self.make_suggestion_item("force", "Force", body, reward, message, 0)
		print(body)
		return rec

	def debugRecommendations(self):
		print("\n\nDEBUG RECOMMENDATIONS---" + str(len(self.userRecommendations)) + " Users\n")
		for user in self.userRecommendations:
			print("User " + user)
			print("---------")
			recList = self.userRecommendations[user]
			for rec in recList:
				print(rec["type"])
				print(rec["title"])
				print(rec["body"])
			print(" ")

	def checkRecommendation(self, user, rec):
		moveTime = 20*60
		reduceTime = 10*60
		forceTime = 30*60
		shiftTime = 12*60*60
		shadeTime = 60*60
		if rec is None or "messageID" not in rec:
			return
		message = rec["messageID"]
		t = rec["type"]
		if (t == "move" and cloudserver.db.pushManagementDispCheck(message, moveTime)):
        	self.userRecommendations[user].append(rec)
        	cloudserver.db.submitRecommendationTimestamp(user, message)
        	continue
        if (t == "reduce" and cloudserver.db.pushManagementDispCheck(message, reduceTime)):
        	self.userRecommendations[user].append(rec)
        	cloudserver.db.submitRecommendationTimestamp(user, message)
        	continue
        if (t == "force" and cloudserver.db.pushManagementDispCheck(message, forceTime)):
        	self.userRecommendations[user].append(rec)
        	cloudserver.db.submitRecommendationTimestamp(user, message)
        	continue
        if (t == "shift" and cloudserver.db.pushManagementDispCheck(message, shiftTime)):
        	self.userRecommendations[user].append(rec)
        	cloudserver.db.submitRecommendationTimestamp(user, message)
        	continue
        if (t == "shade" and cloudserver.db.pushManagementDispCheck(message, shadeTime)):
        	self.userRecommendations[user].append(rec)
        	cloudserver.db.submitRecommendationTimestamp(user, message)
        	continue
		#self.userRecommendations[user].append(rec)



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
		self.getUserLocations()
		self.loadBuildingParams()
		while True:
			self.clearRecommendations()
			#self.runOptimization()
			self.randomRecommendations()
			#self.deepLearning()
			self.debugRecommendations()
			# will print the recommendations to terminal, comment to disable
			time.sleep(self.checkInterval)
			print "Interval"
