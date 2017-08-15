import random
import math
import sys


class simulator:


	def __init__(self):
		###################################################
		## state variable templates
		## self.state/self.nextState = {"room1": ["person 1", "person 2"], "room2" : [], "room3": ["person3"]...}
		## self.parameters = {"person 1": {"SpacePref": {"room1": 85.0, "room2": 10.0, ...}, "Setpoint": 72, "AlonePref": True}, "person2": {...}}
		## self.spaces = {"room1": {"MaxOccupancy":6, "PermanentSpace":True, "AverageConsumption":5000, "ConsumptionOverTime":[199, 205, ...]}, "room2"...}
		#####################################################
		self.bestState = {}
		self.bestEnergyState = -1
		self.state = {}
		self.nextState = {}
		self.parameters = {} #occupant parameters
		self.spaces = {}
		self.loadParameters() #load the occupant parameters
		self.initializeState() #initialize the building configuration
		self.printBestState(self.state)
		#print(self.state)
		self.instantiateGraphics()

	def backspace(self):
		print '\r',


	def costFunction(self, inputState):
		if self.D(inputState) == True:
			energyState = self.E(inputState)
			if (self.bestEnergyState == -1 or energyState < self.bestEnergyState):
				self.bestState = self.duplicateState(inputState)
				self.bestEnergyState = energyState
			return energyState
		else:
			return -1

	def E(self, inputState):
		#Determine the sum of energy footprints
		buildingFootprint = 0
		discomfort = 0
		for room in inputState:
			if len(inputState[room]) > 0:
				buildingFootprint += self.spaces[room]["AverageConsumption"]
		return buildingFootprint


			

	def D(self, inputState):
		for room in inputState:
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




	def P(self, inputState, inputStateNew, temperature):
		currentCost = self.costFunction(inputState)
		newCost = self.costFunction(inputStateNew)
		if newCost == -1:
			return False
		randomNumber = random.random()
		if currentCost > newCost:
			return True
		else:
			if temperature != 0:
				return math.exp(-1.0*(newCost-currentCost)/temperature) > randomNumber
			else:
				return True



	def loadParameters(self):
		self.loadFromCode()
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

	def chooseNextState(self, inputState):
		while (1):
			l = random.choice(list(inputState.keys()))
			if len(inputState[l]) > 0:
				randomPerson = random.choice(inputState[l])
				inputState[l].remove(randomPerson)
				randomRoom = random.choice(list(inputState.keys()))
				inputState[randomRoom].append(randomPerson)
				return


	def duplicateState(self, fromState):
		copyState = {}
		for room in fromState:
			copyState[room] = []
			for person in fromState[room]:
				copyState[room].append(person)
		return copyState

	def simulatedAnnealing(self, kmax):
		for k in range(kmax):
			s = str(round(float(k)/float(kmax)*100.0)) + '%'
			print s,
			sys.stdout.flush()
			self.backspace()

			T = float(k)/float(kmax)
			self.nextState = self.duplicateState(self.state)
			self.chooseNextState(self.nextState)
			if self.P(self.state, self.nextState, T):
				self.state = self.nextState
		self.printBestState(self.bestState)
		return self.bestState

	def instantiateGraphics(self):
		return

	def updateGraphics(self):
		return

	def printBestState(self, printState):
		for room in printState:
			print("\n")
			print(room)
			print("-------------------")
			for person in printState[room]:
				print(person)





	def loadFromCode(self):
		self.parameters['Peter'] = {"SpacePref": {"nwc1003b_a":54.36, "nwc1003b_b":15.25, "nwc1000m_a6":21.2, "nwc10": 1.05},
									"SetpointPref":72, "AlonePref": True}
		self.parameters['Stephen'] = {"SpacePref": {"nwc1003b_b":10.0, "nwc1003b_a":30.0, "nwc1000m_a6":55.0, "nwc10": 1.0}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['Laixi'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10": 1.0}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['Xuanyu'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['Ji'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['Mark'] = {"SpacePref":{"nwc1000m_a1":86.0, "nwc1000m_a2":7.0}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['LeiLei'] = {"SpacePref":{"nwc1000m_a2":89.0, "nwc1000m_a1":7.4}, "SetpointPref":72,
									"AlonePref":False}
		self.parameters['Fred'] = {"SpacePref":{"nwc1008":90.0, "nwc10":10.0}, "SetpointPref":72, "AlonePref":False}

		self.spaces["nwc1003b_a"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":10000}
		self.spaces["nwc1003b_b"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000}
		self.spaces["nwc1000m_a1"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":3000}
		self.spaces["nwc1000m_a2"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000}
		self.spaces["nwc1000m_a6"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":5000}
		self.spaces["nwc10"] = {"MaxOccupancy":1000, "PermanentSpace":False, "AverageConsumption":300}
		self.spaces["nwc1008"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":700}


S = simulator()
S.simulatedAnnealing(100000)















