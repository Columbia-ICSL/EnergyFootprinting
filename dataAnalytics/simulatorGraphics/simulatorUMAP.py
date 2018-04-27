import matplotlib.pyplot as plt
import random
import datetime
import matplotlib.dates as mdates
import math
import sys
import csv
import numpy as np
from graphics import *
import time

_num_bins = 96
win = GraphWin("floorplan", 531, 741)	
b = Image(Point(265, 371), "floorplan.gif")
r = Rectangle(Point(20, 0), Point(511, 150))
r.setFill("white")
title = Text(Point(265, 30), "Building Occupant Optimization")
simTime = Text(Point(265, 100), "Time- Initial Configuration")
simTime.setSize(18)
title.setSize(30)

Image.draw(b, win)
#r.draw(win)
#title.draw(win)
#simTime.draw(win)

class simulator:
	def __init__(self):
		###################################################
		## state variable templates
		## self.state/self.nextState = {"room1": ["person 1", "person 2"], "room2" : [], "room3": ["person3"]...}
		## self.parameters = {"person 1": {"SpacePref": {"room1": 85.0, "room2": 10.0, ...}, "Setpoint": 72, "AlonePref": True}, "person2": {...}}
		## self.spaces = {"room1": {"MaxOccupancy":6, "PermanentSpace":True, "AverageConsumption":5000, "ConsumptionOverTime":[199, 205, ...]}, "room2"...}
		#####################################################
		self.occupantMap = {'Peter':0,
					'Stephen':1,
					'Laixi':2,
					'Xuanyu':3,
					'Ji':4,
					'Mark':5,
					'LeiLei':6,
					'Fred':7,
					'Jiayue':8,
					'Sam':9,
					'Soony':10,
					'Tetsu':11,
					'Mo':12,
					'Teresa':13,
					'Abhi':14,
					'Ankur':15}
		self.QTable = {}

		self.bestState = {}
		self.bestEnergyState = -1
		self.state = {}
		self.nextState = {}
		self.parameters = {} #occupant parameters
		self.spaces = {}
		self.loadParameters() #load the occupant parameters
		
		self.initializeState() #initialize the building configuration
		while not self.D(self.state):
			self.initializeState()
		#self.printBestState(self.state)
		self.bestEnergyList = []
		self.energyList = []
		self.probabilityList = []
		self.temperatureList = []
		#print(self.state)
		self.instantiateGraphics()
		self.currentState = None
		self.schedules = {}
		self.energyFootprints = {}




		self.ExteriorModel = []
		self.InteriorModel = []
		self.weather = []
		self.newWeather = []


	def retrain(self):
		self.bestState = {}
		self.bestEnergyState = -1
		self.QTable = {}
		self.state = {}
		self.nextState = {}
		#self.parameters = {} #occupant parameters
		#self.spaces = {}
		#self.loadParameters() #load the occupant parameters
		self.initializeState() #initialize the building configuration
		while not self.D(self.state):
			self.initializeState() #initialize the building configuration
		#self.printBestState(self.state)
		self.energyList = []
		#print(self.state)
		#self.instantiateGraphics()

	def init(self):
		self.bestState = {}
		self.bestEnergyState = -1
		self.state = {}
		self.nextState = {}
		#self.parameters = {} #occupant parameters
		#self.spaces = {}
		#self.loadParameters() #load the occupant parameters
		self.initializeState() #initialize the building configuration
		while not self.D(self.state):
			self.initializeState() #initialize the building configuration
		#self.printBestState(self.state)
		self.energyList = []
		#print(self.state)
		#self.instantiateGraphics()

	def initStart(self, DoW):
		self.bestState = {}
		self.enterTimes = {}
		self.enterChangeTimes = {}
		self.enterSpace = {}
		self.bestEnergyState = -1
		self.state = {}
		self.nextState = {}
		#self.parameters = {} #occupant parameters
		#self.spaces = {}
		#self.loadParameters() #load the occupant parameters
		self.initializeStateEmpty(DoW) #initialize the building configuration
		while not self.D(self.state):
			self.initializeStateEmpty(DoW) #initialize the building configuration
		#self.printBestState(self.state)
		self.energyList = []
		#print(self.state)
		#self.instantiateGraphics()

	def backspace(self):
		print '\r',

	def costFunction_time(self, inputState, time, normal=False):
		energyState = self.E_time(inputState, time, normal)
		return energyState






	def getMultFactor(self, room, occ, weather):
		O = 0
		if (occ != 0):
			O = occ + 1
		if (room == "OOL"):
			return 1.0
		if (self.spaces[room]["Exterior"]):
			return self.ExteriorModel[O][weather]
		else:
			return self.InteriorModel[O]/self.InteriorModel[1]







	def E_time(self, inputState, time, normal=False):
		#Determine the sum of energy footprints
		buildingFootprint = 0.0
		buildingLights = 0.0
		for room in inputState:
			multFactor = 1.0
			if len(inputState[room]) > 0:
				buildingLights += self.spaces[room]["Lights"]
				multFactor = self.getMultFactor(room, len(inputState[room]), self.newWeather[time])
			elif len(inputState[room]) == 0:
				multFactor = self.getMultFactor(room, 0, self.newWeather[time])
			if normal:
				multFactor = 1.0
			normalizedEnergy = self.spaces[room]["ConsumptionOverTime"][time] * multFactor# * self.Dscore(inputState, room)
			buildingFootprint += normalizedEnergy

		return (buildingFootprint, buildingLights)

	def Dscore(self, inputState, room):
		#normalize to 1 - 1.5
		totalScore = 0.0
		numPersons = 0
		for person in inputState[room]:
			numPersons += 1
			setpointPref = self.parameters[person]["SetpointPref"]
			# if temp differ by 5 degress or more return the max value for now
			if abs(setpointPref - self.spaces[room]["AverageTemp"]) > 5:
				totalScore += 1.5
				# computes parabola?
			else:
				totalScore += 0.1 * math.sqrt(abs(setpointPref - self.spaces[room]["AverageTemp"])) + 1
		return totalScore/numPersons
				#find the discomfort score along the parabola and then normalize to 1-1.5

	def D(self, inputState):
		for room in inputState:
			if room == "OOL":
				continue
			if len(inputState[room]) > 0: #and there are people assigned to the space
				if not self.spaces[room]["PermanentSpace"]: #if the room is not a permanent (e.g. working) space
					return False

			if len(inputState[room]) > self.spaces[room]["MaxOccupancy"]: #if there are too many people in the space
				return False

			for occupant in inputState[room]: #Check that every occupant is in a "comfortable space"
				if (room in self.parameters[occupant]["SpacePref"]):
					spacePreference = self.parameters[occupant]["SpacePref"][room]
					#Do some heuristic on space preference here
					continue
				else:
					return False
		return True

	def P_time(self, inputState, inputStateNew, time):
		currentCost = self.costFunction_time(inputState, time)
		newCost = self.costFunction_time(inputStateNew, time)
		#print (currentCost, newCost)
		return (currentCost, newCost)


	def loadParameters(self):
		self.loadFromCode2()
		for room in self.spaces:
			self.spaces[room]["occupied"] = [None] * len(self.spaces[room]["coordinates"])
		#self.loadFromFile()

	def initializeState(self):
		for space in self.spaces:
			self.state[space] = []
		for occupant in self.parameters:
			cumulative = 0.0
			total = 0.0
			newSpace = ""
			spacePreference = self.parameters[occupant]["SpacePref"]
			for room in spacePreference:
				total += spacePreference[room]
			randomNumber = random.uniform(0, total)
			for room in spacePreference:
				cumulative += spacePreference[room]
				if cumulative >= randomNumber:
					newSpace = room
					self.state[newSpace].append(occupant)
					break

	def initializeStateEmpty(self, DoW):
		for space in self.spaces:
			self.state[space] = []
		for occupant in self.parameters:
			self.state["OOL"].append(occupant)
			self.enterTimes[occupant] = int(round(np.random.normal(self.parameters[occupant]["EnterLab"][DoW], 0,1)))#self.parameters[occupant]["STD"], 1)))
			self.enterChangeTimes[occupant] = self.enterTimes[occupant]
			cumulative = 0.0
			total = 0.0
			newSpace = ""
			spacePreference = self.parameters[occupant]["SpacePref"]
			for room in spacePreference:
				total += spacePreference[room]
			randomNumber = random.uniform(0, total)
			for room in spacePreference:
				cumulative += spacePreference[room]
				if cumulative >= randomNumber:
					newSpace = room
			self.enterSpace[occupant] = newSpace
################################################
## Q-Table functions
################################################

	def stateToDict(self, inputState):
		dictState = [""]*len(self.occupantMap)
		for room in inputState:
			for occupant in inputState[room]:
				dictState[self.occupantMap[occupant]] = room
		DS = ""
		for i in range(len(dictState)):
			DS = DS + dictState[i]
		return DS

	def updateQTable(self, state, nextState, action, reward):
		dictState = self.stateToDict(state)
		if dictState not in self.QTable:
			self.QTable[dictState] = []
			room = self.parameters['Peter']["room"]
			self.QTable[dictState].append(('Peter', room, 0.0))
		for i in range(len(self.QTable[dictState])):
			priorAction = self.QTable[dictState][i]
			priorReward = priorAction[2]
			if (priorAction[0] == action[0] and priorAction[1] == action[1]):
				self.QTable[dictState][i] = (action[0], action[1], 0.2*priorReward + 0.8*(reward + 0.5*self.findMAP(nextState)))
				return
		self.QTable[dictState].append((action[0], action[1], reward))

################################################
## Explore vs. Exploit
################################################

	def findMAP(self, inputState):
		bestAction = None
		dictState = self.stateToDict(inputState)
		MAP = -10000000.0 #perhaps this needs to be -inf, but for now assume Q value is not negative
		if (dictState in self.QTable): #look for the state in the QTable.
			for action in self.QTable[dictState]:
				if action[2] > MAP: #find the best action (The MAP) maximum a posteriori
					MAP = action[2]
					bestAction = action
		if (MAP > 0):
			return MAP
		else:
			return 0

	def movePerson(self, inputState, person, space):
		for room in inputState:
			if person in inputState[room]:
				inputState[room].remove(person)
			inputState[space].append(person)
			return
	
	def chooseNextState(self, inputState): #choose a random action.
		while (1):
			l = random.choice(list(inputState.keys())) #choose a random room
			if len(inputState[l]) > 0: #if there are any people in the room
				randomPerson = random.choice(inputState[l]) #choose a person randomly
				randomRoom = random.choice(list(self.parameters[randomPerson]["SpacePref"].keys())) #choose another random room
				if randomRoom == l:
					continue
				inputState[l].remove(randomPerson)
				inputState[randomRoom].append(randomPerson) #move chosen person to room
				return (randomPerson, randomRoom)

	def chooseBestState(self, inputState): #choose the best action from the ones already explored.
		bestAction = None
		dictState = self.stateToDict(inputState)
		if (dictState in self.QTable): #look for the state in the QTable.
			MAP = -10000000.0 #perhaps this needs to be -inf, but for now assume Q value is not negative
			for action in self.QTable[dictState]:
				if action[2] > MAP: #find the best action (The MAP) maximum a posteriori
					MAP = action[2]
					bestAction = action
			occupant = bestAction[0]
			room = bestAction[1]
			previousRoom = None
			for rm in inputState:
				if occupant in inputState[rm]:
					previousRoom = rm
					break
			assert(occupant in inputState[previousRoom])
			inputState[previousRoom].remove(occupant)
			inputState[room].append(occupant)
		else: #otherwise, we should randomly choose the next state
			bestAction = self.chooseNextState(inputState)
		return bestAction
################################################

	def duplicateState(self, fromState):
		copyState = {}
		for room in fromState:
			copyState[room] = []
			for person in fromState[room]:
				copyState[room].append(person)
		return copyState

	def learnSchedules(self, kmax):
		self.energyNoChange = []
		self.energyChange = []
		self.energyNoChangeCum = []
		self.energyChangeCum = []

		self.energySaved = []
		self.energySavedLights = []
		self.averageEnergy = 0.0
		self.averageEnergyLights = 0.0
		occupant = np.random.randint(len(self.occupantMap))
		for person in self.occupantMap:
			if self.occupantMap[person] == occupant:
				occupant = person
				break
		occupant = "Stephen"
		print("Shifting Occupant " + occupant)
		for k in range(kmax):
			#s = str(float(k)/float(kmax)*100.0) + '%'
			#print s
			self.initStart(4)
			self.enterChangeTimes[occupant] = self.enterTimes[occupant] +4
			self.nextState = self.duplicateState(self.state)
			self.nextChangeState = self.duplicateState(self.state)
			self.noChangeCost = 0.0
			self.changeCost = 0.0
			for t in range(0, 96):
				for person in self.enterTimes:
					if t == self.enterTimes[person]:
						newSpace = self.enterSpace[person]
						self.movePerson(self.nextState, person, newSpace)
				

				(costFootprint, costLights) = self.costFunction_time(self.nextState, t)
				occ = len(self.nextState[self.enterSpace[occupant]])
				print occ
				multFactor = self.getMultFactor(self.enterSpace[occupant], occ, self.newWeather[t])
				normalizedEnergy = self.spaces[self.enterSpace[occupant]]["ConsumptionOverTime"][t] * multFactor
				print "normalized total " + str(costFootprint)
				print "normalized " + str(normalizedEnergy) + " mult factor " + str(multFactor)

				cost = costFootprint + costLights
				self.noChangeCost += cost/4.0
				self.energyNoChangeCum.append(self.noChangeCost)
				#self.energyNoChange.append(cost)
				self.energyNoChange.append(normalizedEnergy)


				for person in self.enterChangeTimes:
					if t == self.enterChangeTimes[person]:
						newSpace = self.enterSpace[person]
						self.movePerson(self.nextChangeState, person, newSpace)


				(newCostFootprint, newCostLights) = self.costFunction_time(self.nextChangeState, t)
				occ = len(self.nextChangeState[self.enterSpace[occupant]])
				print occ
				multFactor = self.getMultFactor(self.enterSpace[occupant], occ, self.newWeather[t])
				normalizedEnergy = self.spaces[self.enterSpace[occupant]]["ConsumptionOverTime"][t] * multFactor
				print "total " + str(newCostFootprint)
				print "normalized " + str(normalizedEnergy) + " mult factor " + str(multFactor)

				newCost = newCostFootprint + newCostLights
				self.changeCost += newCost/4.0
				self.energyChangeCum.append(self.changeCost)
				#self.energyChange.append(newCost)
				self.energyChange.append(normalizedEnergy)
				self.energySaved.append(costFootprint/4.0-newCostFootprint/4.0)
				self.energySavedLights.append(costLights/4.0-newCostLights/4.0)
				print costFootprint-newCostFootprint
		for i in range(len(self.energySaved)):
			self.averageEnergy += self.energySaved[i]
			self.averageEnergyLights += self.energySavedLights[i]
		print("Average Energy Saved " + str(self.averageEnergy/kmax))
		print("Average Energy Saved Lights " + str(self.averageEnergyLights/kmax))
		plt.plot(range(0, 96), self.energyChange, range(0, 96), self.energyNoChange)
		print self.energyChange
		print self.energyNoChange
		


	def reinforcementLearning(self, kmax, epsilon, optimistic=False):
		totalReducedEnergy = []
		for k in range(kmax):
			self.init()
			s = str(float(k)/float(kmax)*100.0) + '%'
			print s
			for t in range(32, 72):
				action = None
				while (1):
					self.nextState = self.duplicateState(self.state)
					##### Determine exploit vs explore #####
					if (random.uniform(0, 1) < epsilon): #explore
						action = self.chooseNextState(self.nextState)
					else: #exploit
						action = self.chooseBestState(self.nextState)

					if self.D(self.nextState) == True: #check that the new state is valid
						break


				# Determine if occupant took action
				occupant = action[0]
				room = action[1]
				probabilityMove = -0.1
				reward = 0.0
				if room in self.parameters[occupant]["SpacePref"]:
					probabilityMove = self.parameters[occupant]["SpacePref"][room]
				if optimistic:
					probabilityMove = 101
				if (random.uniform(0, 1)*100.0 < probabilityMove): #occupant took action
					# Determine reward
					(currentCost, newCost) = self.P_time(self.state, self.nextState, t)
					currentFootprint = currentCost[0]
					currentLights = currentCost[1]
					newFootprint = newCost[0]
					newLights = newCost[1]
					reward = currentFootprint+currentLights-newFootprint-newLights
				else:
					self.nextState = self.state

				# Update Q-Table
				self.updateQTable(self.state, self.nextState, action, reward)
				#print("iteration: " + str(k) + ", time: " + str(t))
				#print(self.QTable[self.stateToDict(self.state)])
				#print(action)
				#print(reward)
				#time.sleep(1)
				self.state = self.nextState #change state
				self.updateGraphics(self.state)
				self.updateGraphics(self.state)

	def testRecommendations2(self, iterations):
		self.energySaved = []
		self.energySavedPeter = []
		action = None
		for i in range(iterations):
			self.init()
			totalEnergySaved = 0.0
			self.nextState = self.duplicateState(self.state)
			self.testState = self.duplicateState(self.state)
			X = np.random.randint(32, 72)
			for t in range(32, 80):
				if t == X:
					while(1):
						#self.testState = self.duplicateState(self.state)
						action = self.chooseBestState(self.testState)
						if self.D(self.testState) == True:
							break
					#self.state = self.testState
				if t == X+8:
					self.testState = self.duplicateState(self.nextState)
				(costFootprint, costLights) = self.costFunction_time(self.testState, t)
				newCost = costFootprint + costLights
				(Footprint, Lights) = self.costFunction_time(self.nextState, t)
				cost = Footprint + Lights
				totalEnergySaved += (cost-newCost)/4.0
			occupant = action[0]
			if abs(totalEnergySaved) < 0.01:
				continue
			self.energySaved.append(totalEnergySaved)
			if occupant == "Peter":
				self.energySavedPeter.append(totalEnergySaved)
		S = sorted(self.energySaved)
		S2 = sorted(self.energySavedPeter)
		print(S)
		print(S2)
		plt.figure()
		plt.plot(range(len(S)), S)

		plt.figure()
		plt.plot(range(len(S2)), S2)
		plt.show()






	def testRecommendations(self, iterations):
		self.arr1 = []
		self.arr2 = []
		self.arr3 = []
		self.arr4 = []
		for i in range(iterations):
			self.testManyRecs()
		print self.arr1
		print self.arr2
		print self.arr3
		print self.arr4
	def testManyRecs(self):
		self.energyNoChange = []
		self.energyChange = []
		self.energyAllChange = []
		self.energyNormal = []

		self.savedEnergyFootprint = []
		self.savedEnergyLights = []

		self.init()
		self.noRecs = self.duplicateState(self.state)
		self.noChangeCost = 0.0
		self.changeCost = 0.0

		self.allRecs = self.duplicateState(self.state)
		self.allCost = 0.0

		self.normalOperation = 0.0
		self.normalOps = self.duplicateState(self.state)

		for t in range(32, 72):
			(costFootprint, costLights) = self.costFunction_time(self.normalOps, t, True)
			cost = costFootprint + costLights
			self.normalOperation += cost/4.0
			self.energyNormal.append(self.normalOperation)
			(costFootprint, costLights) = self.costFunction_time(self.noRecs, t)
			cost = costFootprint + costLights
			self.noChangeCost += cost/4.0
			self.energyNoChange.append(self.noChangeCost)
			while(1):
				self.nextState = self.duplicateState(self.state)
				action = self.chooseBestState(self.nextState)
				if self.D(self.nextState) == True:
					break
			occupant = action[0]
			room = action[1]
			probabilityMove = -0.1
			if room in self.parameters[occupant]["SpacePref"]:
				probabilityMove = self.parameters[occupant]["SpacePref"][room]
			if (random.uniform(0, 1)*100.0 < probabilityMove): #occupant took action
				g = 1
				#print("time: " + str(t))
				#print(action)
				#print("action taken")
			else:
				#print("time: " + str(t))
				#print(action)
				#print("action not taken")
				self.nextState = self.state
			self.state = self.nextState
			(costFootprint, costLights) = self.costFunction_time(self.state, t)
			cost = costFootprint + costLights
			self.changeCost += cost/4.0
			self.energyChange.append(self.changeCost)
			self.savedEnergyFootprint.append(costFootprint)
			self.savedEnergyLights.append(costLights+costFootprint)
			self.updateGraphics(self.state)
			self.updateGraphics(self.state)
			time.sleep(0.01)
		
		for t in range(32, 72):
			(costFootprint, costLights) = self.costFunction_time(self.allRecs, t)
			cost = costFootprint + costLights
			while(1):
				self.nextState = self.duplicateState(self.state)
				action = self.chooseBestState(self.nextState)
				if self.D(self.nextState) == True:
					break
			occupant = action[0]
			room = action[1]
			self.state = self.nextState
			(costFootprint, costLights) = self.costFunction_time(self.state, t)
			cost = costFootprint + costLights
			self.allCost += cost/4.0
			self.energyAllChange.append(self.allCost)

		customdate = datetime.datetime(2017, 3, 1, 8, 0)
		y = [0]*40
		x = [customdate + datetime.timedelta(minutes=15*i) for i in range(len(y))]
		myFmt = mdates.DateFormatter('%H:%M')

		for i in range(len(self.energyNormal)):
			self.energyNoChange[i] = self.energyNormal[i] - self.energyNoChange[i]
			self.energyAllChange[i] = self.energyNormal[i] - self.energyAllChange[i]
			self.energyChange[i] = self.energyNormal[i] - self.energyChange[i]
		print([self.energyNoChange[-1], self.energyChange[-1], self.energyAllChange[-1], self.energyNormal[-1]])
		self.arr1.append(self.energyNoChange[-1])
		self.arr2.append(self.energyChange[-1])
		self.arr3.append(self.energyAllChange[-1])
		self.arr4.append(self.energyNormal[-1])
		plotFigures = False
		if plotFigures:
			plt.figure(1)
			a1, = plt.plot(x, self.energyNoChange, label='No Recommendations')
			a2, = plt.plot(x, self.energyChange, label='Realistic Recommendations')
			a3, = plt.plot(x, self.energyAllChange, label='All Recommendations')
			a4, = plt.plot(x, self.energyNormal, label='Normal Operation')
			plt.gcf().autofmt_xdate()
			plt.gca().xaxis.set_major_formatter(myFmt)
			plt.xlabel('Time of Day')
			plt.ylabel('Total Energy Saving (Wh)')
			plt.title('Comparison of Recommendation Effectiveness')
			plt.legend(handles=[a1, a2, a3])

			self.savedEnergyFootprint = np.array(self.savedEnergyFootprint)
			self.savedEnergyLights = np.array(self.savedEnergyLights)
			y = np.row_stack((self.savedEnergyLights, self.savedEnergyFootprint))
			y_stack = np.cumsum(y, axis=0)
			fig = plt.figure(2)

			ax1 = fig.add_subplot(111)
			ax1.fill_between(x, 0, y_stack[0,:], facecolor="#CC6666", alpha=.7)
			ax1.fill_between(x, y_stack[0,:], y_stack[1,:], facecolor="#1DACD6", alpha=.7)
			plt.gcf().autofmt_xdate()
			plt.gca().xaxis.set_major_formatter(myFmt)
			plt.ylabel('Total Power Consumption (W)')
			plt.xlabel('Time of Day')
			plt.show()
		#a1, = plt.plot(x, self.savedEnergyFootprint, label='HVAC')
		#a2, = plt.plot(x, self.savedEnergyLights, label='Light')




	def instantiateGraphics(self):
		legendY = 60
		legendX = 50 
		for room in self.state:
			occ = len(self.state[room])
			coord = 0
			for person in self.state[room]:
				if "indicator" not in self.parameters[person]:
					self.parameters[person]["indicator"] = Circle(Point(self.spaces[room]["coordinates"][coord][0], self.spaces[room]["coordinates"][coord][1]), 8)
					#self.parameters[person]["indicator"].setFill(color_rgb(145, 187, 255))
					randRed = random.randint(0, 255)
					randGreen = random.randint(0, 255)
					randBlue = random.randint(0, 255)
					self.parameters[person]["indicator"].setFill(color_rgb(randRed, randGreen, randBlue))
					#personText = Text(Point(legendX, legendY), person)
					#personText.setFill(color_rgb(randRed, randGreen, randBlue))
					#personText.draw(win)
					self.parameters[person]["indicator"].draw(win)
					print((room, coord))
					self.spaces[room]["occupied"][coord] = person
					self.parameters[person]["position"] = coord
					self.parameters[person]["room"] = room
					coord += 1
					legendY += 15
					if (legendY > 140):
						legendY = 60
						legendX += 50
		win.getMouse()

#		Peter.move(100, 100)
#		win.getMouse()
		#win.close()
		return

	def updateGraphics(self, state):
		for room in state:
			for person in state[room]:
				oldRoom = self.parameters[person]["room"]
				if (oldRoom == room):
					continue
				#else:
					#print((person, oldRoom, room))
				self.spaces[oldRoom]["occupied"][self.parameters[person]["position"]] = None
				foundPosition = False
				for i in range(len(self.spaces[room]["occupied"])):
					if self.spaces[room]["occupied"][i] is None:
						newCoord = self.spaces[room]["coordinates"][i]
						self.moveTo(self.parameters[person]["indicator"], newCoord[0], newCoord[1])
						self.spaces[room]["occupied"][i] = person
						self.parameters[person]["position"] = i
						self.parameters[person]["room"] = room
						foundPosition = True
						break
				#if not foundPosition:
				#	print("Collision")
				#	print((room, self.spaces[room]["occupied"]))
		#win.getMouse()
		return

	def moveTo(self, person, x, y):
		center = person.getCenter()
		person.move(x - center.getX(), y - center.getY())
		return

	def loadFromCode2(self):
		self.parameters['Peter'] = {"EnterLab": [47, 46, 48, 49, 46], "STD":6, "SpacePref": {"nwc1003b_a":54.36, "nwc1003b_b":15.25, "nwc1000m_a6":21.2, "nwc1003g": 10.0, "nwc10": 1.05},
									"SetpointPref":71, "AlonePref": True, "Accept":0.6}
		self.parameters['Stephen'] = {"EnterLab": [42, 47, 46, 45, 44], "STD":5, "SpacePref": {"nwc1003b_b":10.0, "nwc1003b_a":30.0, "nwc1000m_a6":55.0, "nwc1003g": 10.0, "nwc10": 1.0}, "SetpointPref":69,
									"AlonePref":False, "Accept":0.7}
		self.parameters['Laixi'] = {"EnterLab": [52, 52, 52, 52, 52], "STD":2, "SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10": 1.0}, "SetpointPref":74,
									"AlonePref":False, "Accept":0.7}
		self.parameters['Xuanyu'] = {"EnterLab": [56, 56, 56, 56, 56], "STD":4,"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":77,
									"AlonePref":False, "Accept":0.7}
		self.parameters['Ji'] = {"EnterLab": [40, 52, 40, 52, 40],"STD":2,"SpacePref": { "nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc1003g": 10.0, "nwc10":1.0}, "SetpointPref":78,
									"AlonePref":False, "Accept":0.7}
		self.parameters['Mark'] = {"EnterLab":[59, 46, 53, 52, 48], "STD":2,"SpacePref":{"nwc1000m_a1":86.0, "nwc1000m_a2":7.0}, "SetpointPref":69,
									"AlonePref":False, "Accept":0.1}
		self.parameters['LeiLei'] = {"EnterLab": [36, 36, 36, 36, 36], "STD":2, "SpacePref":{"nwc1000m_a2":89.0, "nwc1000m_a1":7.4}, "SetpointPref":66,
									"AlonePref":False, "Accept":0.1}
		self.parameters['Fred'] = {"EnterLab": [48, 53, 51, 56, 34], "STD":4,"SpacePref":{"nwc1008":90.0, "nwc10":10.0}, "SetpointPref":72, "AlonePref":False, "Accept":0.01}
		self.parameters['Jiayue'] = {"EnterLab": [52, 52, 52, 52, 52], "STD":2,"SpacePref":{"nwc1000m_a2":95.0}, "Accept":0.1}
		self.parameters['Sam'] = {"EnterLab": [56, 56, 56, 56, 56], "STD":2,"SpacePref":{"nwc1000m_a4":90.0, "nwc1003t":10.0}, "Accept":0.2}
		self.parameters['Soony'] = {"EnterLab": [56, 56, 56, 56, 56], "STD":2,"SpacePref":{"nwc1000m_a4":90.0, "nwc1003t":10.0}, "Accept":0.2}
		self.parameters['Tetsu'] = {"EnterLab": [32, 32, 32, 32, 32], "STD":2, "SpacePref":{"nwc1003t":65.0, "nwc1000m_a4":35.0}, "Accept":0.2}
		self.parameters['Abhi'] = {"EnterLab": [56, 56, 56, 56, 56], "STD": 2, "SpacePref":{"nwc1000m_a5":85.0, "nwc1003gb":15.0}, "Accept":0.3}
		self.parameters['Ankur'] = {"EnterLab": [56, 56, 56, 56, 56], "STD": 2, "SpacePref":{"nwc1000m_a5":85.0, "nwc1003gb":15.0}, "Accept":0.3}
		self.parameters['Teresa'] = {"EnterLab": [42, 42, 42, 42, 42], "STD": 2, "SpacePref":{"nwc1003ga":95.0}, "Accept":0.01}
		self.parameters['Mo'] = {"EnterLab": [42, 42, 42, 42, 42], "STD": 2, "SpacePref":{"nwc1003ga":95.0}, "Accept":0.1}

		self.averageSpaceLoads()


	def loadBuildingModel(self):
		self.ExteriorModel = []
		with open('lab1.csv', 'rb') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
			for row in spamreader:
				self.ExteriorModel.append(list(row))

		for row in range(len(self.ExteriorModel)):
			for col in range(len(self.ExteriorModel[row])):
				if self.ExteriorModel[row][col] == 'NaN':
					self.ExteriorModel[row][col] = 1.0
				else:
					self.ExteriorModel[row][col] = float(self.ExteriorModel[row][col])
		print self.ExteriorModel
		self.InteriorModel = [0.9654,    0.9927,    1.0000,    0.9957,    0.9915,    0.9879]
		self.weather = []
		with open('weather.csv', 'rb') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
			for row in spamreader:
				self.weather = list(row)
				break
		self.timestamps = []
		self.newWeather = []
		for i in range(24):
			for j in range(4):
				self.newWeather.append(int(round(float(self.weather[i]))))

	def multiplier(self):
		for i in range(len(self.spaces["nwc1003b_a"]["ConsumptionOverTime"])):
			self.spaces["nwc1003b_a"]["ConsumptionOverTime"][i] = self.spaces["nwc1003b_a"]["ConsumptionOverTime"][i]*5
			self.spaces["nwc1003b_b"]["ConsumptionOverTime"][i] = self.spaces["nwc1003b_b"]["ConsumptionOverTime"][i]*5
			self.spaces["nwc1003t"]["ConsumptionOverTime"][i] = self.spaces["nwc1003t"]["ConsumptionOverTime"][i]*5
			self.spaces["nwc1003burke"]["ConsumptionOverTime"][i] = self.spaces["nwc1003burke"]["ConsumptionOverTime"][i]*5

	def averageSpaceLoads(self):
		self.spaces["nwc1003b_a"] = {"Exterior":True, "MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":10000, "AverageTemp":73, "ConsumptionOverTime":
		[570, 567, 562, 568, 563, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038,
		722, 617, 607, 752, 1427, 1568, 1578, 1570, 1478, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2640, 979, 809,
		1182, 3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 764, 619, 477, 552, 690, 509, 540, 552, 561, 561, 563,
		563, 566, 554, 557, 560, 549, 563, 565, 574, 572, 562, 563, 550, 557, 558], "Lights": 140, "coordinates": [(8, 499), (24, 499), (40, 499), (56, 499)]}
		self.spaces["nwc1003b_b"] = {"Exterior":True, "MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000, "AverageTemp":70, "ConsumptionOverTime":
		[570, 568, 562, 568, 564, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038, 722,
		617, 607, 752, 1427, 1568, 1578, 1570, 1479, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2641, 979, 809, 1182,
		3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 765, 619, 477, 553, 690, 510, 541, 552, 561, 561, 563, 564,
		567, 554, 558, 560, 550, 563, 566, 574, 572, 562, 563, 551, 557, 559], "Lights": 140, "coordinates": [(8, 539), (24, 539), (40, 539), (56, 539)]}
		self.spaces["nwc1003t"] = {"Exterior":True, "MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000, "AverageTemp":70, "ConsumptionOverTime":
		[570, 568, 562, 568, 564, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038, 722,
		617, 607, 752, 1427, 1568, 1578, 1570, 1479, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2641, 979, 809, 1182,
		3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 765, 619, 477, 553, 690, 510, 541, 552, 561, 561, 563, 564,
		567, 554, 558, 560, 550, 563, 566, 574, 572, 562, 563, 551, 557, 559], "Lights": 280, "coordinates": [(8, 459), (24, 459), (40, 459), (56, 459)]}
		self.spaces["nwc1003burke"] = {"Exterior":True, "MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000, "AverageTemp":70, "ConsumptionOverTime":
		[570, 568, 562, 568, 564, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038, 722,
		617, 607, 752, 1427, 1568, 1578, 1570, 1479, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2641, 979, 809, 1182,
		3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 765, 619, 477, 553, 690, 510, 541, 552, 561, 561, 563, 564,
		567, 554, 558, 560, 550, 563, 566, 574, 572, 562, 563, 551, 557, 559], "Lights": 280, "coordinates": [(8, 419), (24, 419), (40, 419), (56, 419)]}
		
		self.spaces["nwc1003g"] = {"Exterior":False, "MaxOccupancy":5, "PermanentSpace":True, "AverageConsumption": 1000, "AverageTemp": 74, "ConsumptionOverTime":
		[91, 91, 90, 92, 90, 92, 90, 90, 92, 91, 89, 89, 89, 91, 89, 89, 89, 90, 88, 90, 86, 88, 86, 87, 98, 411, 568, 567, 399, 342, 327, 407, 854,
		1068, 1070, 1089, 1023, 1763, 1827, 1411, 1042, 1134, 1718, 2515, 745, 867, 458, 433, 365, 549, 507, 589, 2787, 4301, 2517, 1682, 1204, 562, 450, 818,
		426, 439, 459, 511, 431, 440, 467, 469, 521, 465, 515, 373, 190, 132, 116, 90, 93, 92, 92, 93, 93, 92, 93, 92, 92, 93, 91, 92, 92, 94, 93, 90, 92, 89, 92, 90], "Lights": 112, "coordinates": [(84, 499), (100, 499), (84, 529), (100, 529)]}
		self.spaces["nwc1003ga"] = {"Exterior":False, "MaxOccupancy":5, "PermanentSpace":True, "AverageConsumption": 1000, "AverageTemp": 74, "ConsumptionOverTime":
		[91, 91, 90, 92, 90, 92, 90, 90, 92, 91, 89, 89, 89, 91, 89, 89, 89, 90, 88, 90, 86, 88, 86, 87, 98, 411, 568, 567, 399, 342, 327, 407, 854,
		1068, 1070, 1089, 1023, 1763, 1827, 1411, 1042, 1134, 1718, 2515, 745, 867, 458, 433, 365, 549, 507, 589, 2787, 4301, 2517, 1682, 1204, 562, 450, 818,
		426, 439, 459, 511, 431, 440, 467, 469, 521, 465, 515, 373, 190, 132, 116, 90, 93, 92, 92, 93, 93, 92, 93, 92, 92, 93, 91, 92, 92, 94, 93, 90, 92, 89, 92, 90],
		"Lights": 112, "coordinates": [(84, 499), (100, 499), (84, 529), (100, 529)]}
		self.spaces["nwc1003gb"] = {"Exterior":False, "MaxOccupancy":5, "PermanentSpace":True, "AverageConsumption": 1000, "AverageTemp": 74, "ConsumptionOverTime":
		[91, 91, 90, 92, 90, 92, 90, 90, 92, 91, 89, 89, 89, 91, 89, 89, 89, 90, 88, 90, 86, 88, 86, 87, 98, 411, 568, 567, 399, 342, 327, 407, 854,
		1068, 1070, 1089, 1023, 1763, 1827, 1411, 1042, 1134, 1718, 2515, 745, 867, 458, 433, 365, 549, 507, 589, 2787, 4301, 2517, 1682, 1204, 562, 450, 818,
		426, 439, 459, 511, 431, 440, 467, 469, 521, 465, 515, 373, 190, 132, 116, 90, 93, 92, 92, 93, 93, 92, 93, 92, 92, 93, 91, 92, 92, 94, 93, 90, 92, 89, 92, 90],
		"Lights": 112, "coordinates": [(84, 499), (100, 499), (84, 529), (100, 529)]}
		
		self.spaces["nwc1000m_a1"] = {"Exterior":True, "MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":3000, "AverageTemp":72, "ConsumptionOverTime":
		[235, 236, 239, 236, 236, 236, 236, 236, 236, 236, 236, 236, 235, 236, 235, 235, 235, 235, 235, 235, 234, 235, 234, 235, 235, 235, 235, 235,
		235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 236, 236, 236, 237, 239, 237, 237, 236, 237, 236, 237, 238, 237, 238, 237, 238, 237,
		237, 237, 237, 237, 236, 235, 235, 235, 235, 237, 237, 236, 236, 236, 235, 235, 235, 236, 235, 236, 235, 236, 236, 236, 236, 236, 236, 236, 236,
		235, 236, 236, 237, 236, 236, 235, 235, 235, 235], "Lights": 60, "coordinates": [(484, 343), (500, 343), (484, 359), (500, 359)]}
		self.spaces["nwc1000m_a2"] = {"Exterior":True, "MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000, "AverageTemp":67, "ConsumptionOverTime":
		[234, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 234, 234, 235, 234, 235, 234, 235, 234, 234, 234, 234, 234, 234, 234,
		234, 234, 234, 234, 234, 234, 234, 234, 234, 234, 233, 234, 235, 235, 235, 235, 235, 238, 236, 236, 235, 236, 236, 236, 237, 236, 237, 236,
		237, 236, 236, 236, 236, 236, 235, 234, 234, 234, 234, 236, 236, 235, 235, 235, 234, 234, 234, 235, 235, 235, 235, 235, 235, 235, 235, 235,
		235, 235, 235, 234, 235, 235, 236, 235, 235, 234, 234], "Lights": 60, "coordinates": [(484, 379), (500, 379), (484, 395), (500, 395)]}
		self.spaces["nwc1000m_a4"] = {"Exterior":True, "MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000, "AverageTemp":67, "ConsumptionOverTime":
		[234, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 234, 234, 235, 234, 235, 234, 235, 234, 234, 234, 234, 234, 234, 234,
		234, 234, 234, 234, 234, 234, 234, 234, 234, 234, 233, 234, 235, 235, 235, 235, 235, 238, 236, 236, 235, 236, 236, 236, 237, 236, 237, 236,
		237, 236, 236, 236, 236, 236, 235, 234, 234, 234, 234, 236, 236, 235, 235, 235, 234, 234, 234, 235, 235, 235, 235, 235, 235, 235, 235, 235,
		235, 235, 235, 234, 235, 235, 236, 235, 235, 234, 234], "Lights": 60, "coordinates": [(484, 458), (500, 458), (484, 474), (500, 474)]}
		self.spaces["nwc1000m_a5"] = {"Exterior":True, "MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000, "AverageTemp":67, "ConsumptionOverTime":
		[234, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 234, 234, 235, 234, 235, 234, 235, 234, 234, 234, 234, 234, 234, 234,
		234, 234, 234, 234, 234, 234, 234, 234, 234, 234, 233, 234, 235, 235, 235, 235, 235, 238, 236, 236, 235, 236, 236, 236, 237, 236, 237, 236,
		237, 236, 236, 236, 236, 236, 235, 234, 234, 234, 234, 236, 236, 235, 235, 235, 234, 234, 234, 235, 235, 235, 235, 235, 235, 235, 235, 235,
		235, 235, 235, 234, 235, 235, 236, 235, 235, 234, 234], "Lights": 60, "coordinates": [(484, 498), (500, 498), (484, 514), (500, 514)]}
		self.spaces["nwc1000m_a6"] = {"Exterior":True, "MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":5000, "AverageTemp":75, "ConsumptionOverTime":
		[235, 236, 236, 235, 235, 235, 235, 236, 237, 235, 235, 235, 234, 236, 235, 234, 234, 234, 237, 235, 233, 234, 233, 236, 234, 234, 236, 236,
		236, 240, 238, 243, 238, 238, 240, 240, 238, 237, 239, 239, 239, 239, 238, 240, 241, 242, 241, 243, 241, 242, 239, 241, 242, 241, 239, 242,
		238, 241, 239, 237, 241, 236, 237, 238, 235, 237, 237, 238, 235, 235, 237, 236, 234, 237, 235, 235, 235, 236, 235, 237, 235, 236, 236, 237,
		235, 237, 235, 236, 236, 236, 236, 235, 235, 235, 234, 234], "Lights": 60, "coordinates": [(484, 539), (500, 539), (484, 555), (500, 555)]}
		self.spaces["nwc10"] = {"Exterior":False, "MaxOccupancy":1000, "PermanentSpace":False, "AverageConsumption":300, "AverageTemp":60, "ConsumptionOverTime":
		[178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 
		177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 
		178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 
		177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176], "Lights": 60, "coordinates": []}
		self.spaces["nwc1008"] = {"Exterior":True, "MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":700, "AverageTemp":70, "ConsumptionOverTime":
		[174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173], "Lights": 100, "coordinates": [(204, 509), (220, 509)]}
		self.spaces["OOL"] = {"Exterior":True, "MaxOccupancy":1000, "PermanentSpace":True, "AverageConsumption":0, "ConsumptionOverTime":[0]*96, "Lights":0, "coordinates":[(10, 10), (30, 30), (50, 50), (70, 70), (90, 90), (110, 110), (130, 130), (150, 150), (170, 170)]}
S = simulator()
S.loadBuildingModel()
#S.multiplier()
#S.learnSchedules(1)




S.reinforcementLearning(100, 0.5, True)
S.testRecommendations(100)
#S.testRecommendations2(100000)
