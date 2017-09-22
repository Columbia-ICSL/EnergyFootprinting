import matplotlib.pyplot as plt
import random
import math
import sys
from graphics import *

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
r.draw(win)
title.draw(win)
simTime.draw(win)

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
		while not self.D(self.state):
			self.initializeState()
		self.printBestState(self.state)
		self.bestEnergyList = []
		self.energyList = []
		self.probabilityList = []
		self.temperatureList = []
		#print(self.state)
		self.instantiateGraphics()
		self.currentState = None
		self.schedules = {}
		self.energyFootprints = {}

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
		
	def plotRoomEnergy(self, label1, label2):
		data1 = self.spaces[label1]["ConsumptionOverTime"]
		data2 = self.spaces[label2]["ConsumptionOverTime"]
		time = range(len(data1))
		plt.plot(time, data1, 'r', time, data2, 'b')
		plt.title("Energy Curves for Two Rooms")
		plt.xlabel("Time (15 minutes)")
		plt.ylabel("Power (W)")
		plt.legend([label1, label2])
		plt.show()
		return
		
	def updateSchedules(self, newState):
		for room in newState:
			for person in newState[room]:
				if person not in self.schedules:
					self.schedules[person] = []
				self.schedules[person].append(room)
		return

	def energyFootprint(self, state, time):
		for room in state:
			occupancy = len(state[room])
			for person in state[room]:
				if person not in self.energyFootprints:
					self.energyFootprints[person] = []
				self.energyFootprints[person].append(self.spaces[room]["ConsumptionOverTime"][time]/occupancy)
		return

	def printEnergyFootprint(self, person):
		previousRoom = ""
		times = []
		for i in range(len(self.schedules[person])):
				newRoom = self.schedules[person][i]
				if (newRoom != previousRoom):
					times.append(i-1)#print("Move to: " + newRoom + " " + "at time" + str(i))
				previousRoom = newRoom
		footprint = self.energyFootprints[person]
		plt.plot(footprint)
		plt.title("Energy Footprint for " + person)
		plt.xlabel("Time (15 min)")
		plt.ylabel("Power (W)")
		for time in times:
			plt.axvline(x=time, color = 'r')
		plt.show()
		return

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

	def costFunction_time(self, inputState, time):
		if self.D(inputState) == True:
			energyState = self.E_time(inputState, time)
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
				buildingFootprint += self.spaces[room]["AverageConsumption"]* self.Dscore(inputState, room)
		return buildingFootprint

	def E_time(self, inputState, time):
		#Determine the sum of energy footprints
		buildingFootprint = 0
		discomfort = 0

		for room in inputState:
			if len(inputState[room]) > 0:
				normalizedEnergy = self.spaces[room]["ConsumptionOverTime"][time] * self.Dscore(inputState, room)
				buildingFootprint += normalizedEnergy
		return buildingFootprint

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
		if currentCost >= newCost:
			self.energyList.append(newCost)
			return True
		else:
			if temperature != 0:
				#tempProbability = math.exp(-1.0*float((newCost-currentCost))/float(temperature))
				#tempProbability = math.exp(-1.0*(1.0-float(currentCost)/float(newCost))*float(temperature))
				#print((newCost-currentCost,temperature, tempProbability))
				#self.probabilityList.append(tempProbability)
				if temperature > randomNumber:
					self.energyList.append(newCost)
					return True
				else:
					self.energyList.append(currentCost)
					return False
			else:
				self.energyList.append(newCost)
				return True

	def P_time(self, inputState, inputStateNew, temperature, time):
		currentCost = self.costFunction_time(inputState, time)
		newCost = self.costFunction_time(inputStateNew, time)
		if newCost == -1:
			return False
		randomNumber = random.random()
		if currentCost > newCost:
			return True
		else:
			if temperature != 0:
				return True#math.exp(-1.0*(newCost-currentCost)/temperature) > randomNumber
			else:
				return True

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
			
			#T = float(k)/float(kmax)
			T = 1.0*(0.999**k)
			self.temperatureList.append(T)
			self.nextState = self.duplicateState(self.state)
			self.chooseNextState(self.nextState)
			if self.P(self.state, self.nextState, T):
				self.state = self.nextState
			self.bestEnergyList.append(self.bestEnergyState)
		self.printBestState(self.bestState)
		plt.plot(self.bestEnergyList[1:100])
		plt.ylabel('Total Power (W)')
		plt.xlabel('Iteration')
		plt.title('Best Energy State To Iteration')
		plt.show()
		plt.plot(self.energyList)
		plt.ylabel('Total Power (W)')
		plt.xlabel('Iteration')
		plt.title('Sample Energy States')
		plt.show()
		#plt.plot(self.probabilityList)
		#plt.show()
		plt.ylabel('Temperature')
		plt.xlabel('Iteration')
		plt.title('Temperature')
		plt.plot(self.temperatureList)
		plt.show()
		return self.bestState

	def timedSimulatedAnnealing(self, kmax):
		for t in range(32, 72):#range(_num_bins):
			self.init()
			print("iteration " + str(t))
			minuteStr = "00"
			if t%4 != 0:
				minuteStr = str((t%4)*15)
			simTime.setText("Time- " + str(t/4) + ":" + minuteStr)

			for k in range(kmax):
				s = str(round(float(k)/float(kmax)*100.0)) + '%'
				print s,
				sys.stdout.flush()
				self.backspace()
				self.energyList.append(self.bestEnergyState)

				Temp = float(k)/float(kmax)
				self.nextState = self.duplicateState(self.state)
				self.chooseNextState(self.nextState)
				if self.P_time(self.state, self.nextState, Temp, t):
					self.state = self.nextState
			if self.currentState is None:
				self.currentState = self.duplicateState(self.bestState)
				self.printBestState(self.currentState)
				self.updateSchedules(self.currentState)
				continue
			startLoc = {}
			endLoc = {}

			currentEnergy = self.E_time(self.currentState, t)
			bestEnergy = self.E_time(self.bestState, t)
			#(bestEnergy, currentEnergy) = self.E_time2(self.bestState, self.currentState, time)
			if (currentEnergy-bestEnergy > 0.01):
				print("Found better Schedule")
				#self.E_time2(self.bestState, self.currentState, time)
				#print((bestEnergy,currentEnergy))
				self.currentState = self.duplicateState(self.bestState)
				self.printBestState(self.currentState)
				#for room in self.currentState:
				#    for person in self.currentState[room]:
				#        startLoc[person] = room
				#for room in self.bestState:
				#    for person in self.bestState[room]:
				#        endLoc[person] = room

				#for person in startLoc:
				#    if (startLoc[person] != endLoc[person]):
				#        print((startLoc[person], endLoc[person], person))
			self.updateSchedules(self.currentState)
			self.energyFootprint(self.currentState, t)
			self.updateGraphics(self.currentState)
			self.updateGraphics(self.currentState)
			time.sleep(0.5)
		self.printSchedules()
		print("Plotting Room Energy...")
		self.plotRoomEnergy("nwc1003b_a", "nwc1003g")
		print("Plotting Energy Energy Footprint...")
		self.printEnergyFootprint("Peter")
						
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
					personText = Text(Point(legendX, legendY), person)
					personText.setFill(color_rgb(randRed, randGreen, randBlue))
					personText.draw(win)
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
				else:
					print((person, oldRoom, room))
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
				if not foundPosition:
					print("PROBLEM")
					print((room, self.spaces[room]["occupied"]))
		#win.getMouse()
		return

	def printBestState(self, printState):
		for room in printState:
			print("\n")
			print(str(room) + " " + str(self.spaces[room]["AverageTemp"]))
			print("-------------------")
			for person in printState[room]:
				print(str(person) + " " + str(self.parameters[person]["SetpointPref"]))

	def printSchedules(self):
		for person in self.schedules:
			print("Schedule for: " + person)
			previousRoom = ""
			if (len(self.schedules[person]) != _num_bins):
				print("Not enough bins! " + person + " " + str(len(self.schedules[person])))
				#assert(self.schedules[person] == _num_bins)
			for i in range(len(self.schedules[person])):
				newRoom = self.schedules[person][i]
				if (newRoom != previousRoom):
					print("Move to: " + newRoom + " " + "at time" + str(i))
				previousRoom = newRoom
		return
				


	def moveTo(self, person, x, y):
		center = person.getCenter()
		person.move(x - center.getX(), y - center.getY())
		return


	def loadFromCode(self):
		self.parameters['Peter'] = {"SpacePref": {"nwc1003b_a":54.36, "nwc1003b_b":15.25, "nwc1000m_a6":21.2, "nwc10": 1.05},
									"SetpointPref":71, "AlonePref": True}
		self.parameters['Stephen'] = {"SpacePref": {"nwc1003b_b":10.0, "nwc1003b_a":30.0, "nwc1000m_a6":55.0, "nwc10": 1.0}, "SetpointPref":69,
									"AlonePref":False}
		self.parameters['Laixi'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10": 1.0}, "SetpointPref":74,
									"AlonePref":False}
		self.parameters['Xuanyu'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":77,
									"AlonePref":False}
		self.parameters['Ji'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":78,
									"AlonePref":False}
		self.parameters['Mark'] = {"SpacePref":{"nwc1000m_a1":86.0, "nwc1000m_a2":7.0}, "SetpointPref":69,
									"AlonePref":False}
		self.parameters['LeiLei'] = {"SpacePref":{"nwc1000m_a2":89.0, "nwc1000m_a1":7.4}, "SetpointPref":66,
									"AlonePref":False}
		self.parameters['Fred'] = {"SpacePref":{"nwc1008":90.0, "nwc10":10.0}, "SetpointPref":72, "AlonePref":False}

		self.spaces["nwc1003b_a"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":10000, "AverageTemp":73, "ConsumptionOverTime":
		[570, 567, 562, 568, 563, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038,
		722, 617, 607, 752, 1427, 1568, 1578, 1570, 1478, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2640, 979, 809,
		1182, 3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 764, 619, 477, 552, 690, 509, 540, 552, 561, 561, 563,
		563, 566, 554, 557, 560, 549, 563, 565, 574, 572, 562, 563, 550, 557, 558], "coordinates": [(8, 499), (24, 499), (40, 499), (56, 499)]}
		self.spaces["nwc1003b_b"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000, "AverageTemp":70, "ConsumptionOverTime":
		[570, 568, 562, 568, 564, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038, 722,
		617, 607, 752, 1427, 1568, 1578, 1570, 1479, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2641, 979, 809, 1182,
		3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 765, 619, 477, 553, 690, 510, 541, 552, 561, 561, 563, 564,
		567, 554, 558, 560, 550, 563, 566, 574, 572, 562, 563, 551, 557, 559], "coordinates": [(8, 539), (24, 539), (40, 539), (56, 539)]}
		#self.spaces["nwc1003g"] = {"MaxOccupancy":5, "PermanentSpace":True, "AverageConsumption": 1000, "AverageTemp": 74, "ConsumptionOverTime":
		#[91, 91, 90, 92, 90, 92, 90, 90, 92, 91, 89, 89, 89, 91, 89, 89, 89, 90, 88, 90, 86, 88, 86, 87, 98, 411, 568, 567, 399, 342, 327, 407, 854,
		#1068, 1070, 1089, 1023, 1763, 1827, 1411, 1042, 1134, 1718, 2515, 745, 867, 458, 433, 365, 549, 507, 589, 2787, 4301, 2517, 1682, 1204, 562, 450, 818,
		#426, 439, 459, 511, 431, 440, 467, 469, 521, 465, 515, 373, 190, 132, 116, 90, 93, 92, 92, 93, 93, 92, 93, 92, 92, 93, 91, 92, 92, 94, 93, 90, 92, 89, 92, 90]}
		self.spaces["nwc1000m_a1"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":3000, "AverageTemp":72, "ConsumptionOverTime":
		[235, 236, 239, 236, 236, 236, 236, 236, 236, 236, 236, 236, 235, 236, 235, 235, 235, 235, 235, 235, 234, 235, 234, 235, 235, 235, 235, 235,
		235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 236, 236, 236, 237, 239, 237, 237, 236, 237, 236, 237, 238, 237, 238, 237, 238, 237,
		237, 237, 237, 237, 236, 235, 235, 235, 235, 237, 237, 236, 236, 236, 235, 235, 235, 236, 235, 236, 235, 236, 236, 236, 236, 236, 236, 236, 236,
		235, 236, 236, 237, 236, 236, 235, 235, 235, 235], "coordinates": [(484, 343), (500, 343), (484, 359), (500, 359)]}
		self.spaces["nwc1000m_a2"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000, "AverageTemp":67, "ConsumptionOverTime":
		[234, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 234, 234, 235, 234, 235, 234, 235, 234, 234, 234, 234, 234, 234, 234,
		234, 234, 234, 234, 234, 234, 234, 234, 234, 234, 233, 234, 235, 235, 235, 235, 235, 238, 236, 236, 235, 236, 236, 236, 237, 236, 237, 236,
		237, 236, 236, 236, 236, 236, 235, 234, 234, 234, 234, 236, 236, 235, 235, 235, 234, 234, 234, 235, 235, 235, 235, 235, 235, 235, 235, 235,
		235, 235, 235, 234, 235, 235, 236, 235, 235, 234, 234], "coordinates": [(484, 379), (500, 379), (484, 395), (500, 395)]}
		self.spaces["nwc1000m_a6"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":5000, "AverageTemp":75, "ConsumptionOverTime":
		[235, 236, 236, 235, 235, 235, 235, 236, 237, 235, 235, 235, 234, 236, 235, 234, 234, 234, 237, 235, 233, 234, 233, 236, 234, 234, 236, 236,
		236, 240, 238, 243, 238, 238, 240, 240, 238, 237, 239, 239, 239, 239, 238, 240, 241, 242, 241, 243, 241, 242, 239, 241, 242, 241, 239, 242,
		238, 241, 239, 237, 241, 236, 237, 238, 235, 237, 237, 238, 235, 235, 237, 236, 234, 237, 235, 235, 235, 236, 235, 237, 235, 236, 236, 237,
		235, 237, 235, 236, 236, 236, 236, 235, 235, 235, 234, 234], "coordinates": [(484, 539), (500, 539), (484, 555), (500, 555)]}
		self.spaces["nwc10"] = {"MaxOccupancy":1000, "PermanentSpace":False, "AverageConsumption":300, "AverageTemp":60, "ConsumptionOverTime":
		[178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 
		177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 
		178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 
		177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176], "coordinates": []}
		self.spaces["nwc1008"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":700, "AverageTemp":70, "ConsumptionOverTime":
		[174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173], "coordinates": [(204, 509)]}
	def loadFromCode2(self):
		self.parameters['Peter'] = {"SpacePref": {"nwc1003b_a":54.36, "nwc1003b_b":15.25, "nwc1000m_a6":21.2, "nwc1003g": 10.0, "nwc10": 1.05},
									"SetpointPref":71, "AlonePref": True}
		self.parameters['Stephen'] = {"SpacePref": {"nwc1003b_b":10.0, "nwc1003b_a":30.0, "nwc1000m_a6":55.0, "nwc1003g": 10.0, "nwc10": 1.0}, "SetpointPref":69,
									"AlonePref":False}
		self.parameters['Laixi'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10": 1.0}, "SetpointPref":74,
									"AlonePref":False}
		self.parameters['Xuanyu'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc10":1.0}, "SetpointPref":77,
									"AlonePref":False}
		self.parameters['Ji'] = {"SpacePref": {"nwc1003b_a":1.0, "nwc1000m_a6":85.0, "nwc1003g": 10.0, "nwc10":1.0}, "SetpointPref":78,
									"AlonePref":False}
		self.parameters['Mark'] = {"SpacePref":{"nwc1000m_a1":86.0, "nwc1000m_a2":7.0}, "SetpointPref":69,
									"AlonePref":False}
		self.parameters['LeiLei'] = {"SpacePref":{"nwc1000m_a2":89.0, "nwc1000m_a1":7.4}, "SetpointPref":66,
									"AlonePref":False}
		self.parameters['Fred'] = {"SpacePref":{"nwc1008":90.0, "nwc10":10.0}, "SetpointPref":72, "AlonePref":False}

		self.spaces["nwc1003b_a"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":10000, "AverageTemp":73, "ConsumptionOverTime":
		[570, 567, 562, 568, 563, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038,
		722, 617, 607, 752, 1427, 1568, 1578, 1570, 1478, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2640, 979, 809,
		1182, 3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 764, 619, 477, 552, 690, 509, 540, 552, 561, 561, 563,
		563, 566, 554, 557, 560, 549, 563, 565, 574, 572, 562, 563, 550, 557, 558], "coordinates": [(8, 499), (24, 499), (40, 499), (56, 499)]}
		self.spaces["nwc1003b_b"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":9000, "AverageTemp":70, "ConsumptionOverTime":
		[570, 568, 562, 568, 564, 568, 564, 565, 566, 566, 562, 557, 555, 555, 550, 559, 566, 568, 560, 563, 559, 562, 559, 561, 571, 943, 1077, 1038, 722,
		617, 607, 752, 1427, 1568, 1578, 1570, 1479, 2185, 2319, 1811, 1515, 1737, 2602, 5745, 5247, 4832, 1790, 1870, 1708, 1744, 2641, 979, 809, 1182,
		3640, 3525, 2067, 1070, 917, 1409, 1215, 1074, 1103, 903, 663, 706, 722, 696, 742, 713, 765, 619, 477, 553, 690, 510, 541, 552, 561, 561, 563, 564,
		567, 554, 558, 560, 550, 563, 566, 574, 572, 562, 563, 551, 557, 559], "coordinates": [(8, 539), (24, 539), (40, 539), (56, 539)]}
		self.spaces["nwc1003g"] = {"MaxOccupancy":5, "PermanentSpace":True, "AverageConsumption": 1000, "AverageTemp": 74, "ConsumptionOverTime":
		[91, 91, 90, 92, 90, 92, 90, 90, 92, 91, 89, 89, 89, 91, 89, 89, 89, 90, 88, 90, 86, 88, 86, 87, 98, 411, 568, 567, 399, 342, 327, 407, 854,
		1068, 1070, 1089, 1023, 1763, 1827, 1411, 1042, 1134, 1718, 2515, 745, 867, 458, 433, 365, 549, 507, 589, 2787, 4301, 2517, 1682, 1204, 562, 450, 818,
		426, 439, 459, 511, 431, 440, 467, 469, 521, 465, 515, 373, 190, 132, 116, 90, 93, 92, 92, 93, 93, 92, 93, 92, 92, 93, 91, 92, 92, 94, 93, 90, 92, 89, 92, 90],
		"coordinates": [(84, 499), (100, 499), (84, 529), (100, 529)]}
		
		self.spaces["nwc1000m_a1"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":3000, "AverageTemp":72, "ConsumptionOverTime":
		[235, 236, 239, 236, 236, 236, 236, 236, 236, 236, 236, 236, 235, 236, 235, 235, 235, 235, 235, 235, 234, 235, 234, 235, 235, 235, 235, 235,
		235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 236, 236, 236, 237, 239, 237, 237, 236, 237, 236, 237, 238, 237, 238, 237, 238, 237,
		237, 237, 237, 237, 236, 235, 235, 235, 235, 237, 237, 236, 236, 236, 235, 235, 235, 236, 235, 236, 235, 236, 236, 236, 236, 236, 236, 236, 236,
		235, 236, 236, 237, 236, 236, 235, 235, 235, 235], "coordinates": [(484, 343), (500, 343), (484, 359), (500, 359)]}
		self.spaces["nwc1000m_a2"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":4000, "AverageTemp":67, "ConsumptionOverTime":
		[234, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 235, 234, 235, 235, 234, 234, 235, 234, 235, 234, 235, 234, 234, 234, 234, 234, 234, 234,
		234, 234, 234, 234, 234, 234, 234, 234, 234, 234, 233, 234, 235, 235, 235, 235, 235, 238, 236, 236, 235, 236, 236, 236, 237, 236, 237, 236,
		237, 236, 236, 236, 236, 236, 235, 234, 234, 234, 234, 236, 236, 235, 235, 235, 234, 234, 234, 235, 235, 235, 235, 235, 235, 235, 235, 235,
		235, 235, 235, 234, 235, 235, 236, 235, 235, 234, 234], "coordinates": [(484, 379), (500, 379), (484, 395), (500, 395)]}
		self.spaces["nwc1000m_a6"] = {"MaxOccupancy":4, "PermanentSpace":True, "AverageConsumption":5000, "AverageTemp":75, "ConsumptionOverTime":
		[235, 236, 236, 235, 235, 235, 235, 236, 237, 235, 235, 235, 234, 236, 235, 234, 234, 234, 237, 235, 233, 234, 233, 236, 234, 234, 236, 236,
		236, 240, 238, 243, 238, 238, 240, 240, 238, 237, 239, 239, 239, 239, 238, 240, 241, 242, 241, 243, 241, 242, 239, 241, 242, 241, 239, 242,
		238, 241, 239, 237, 241, 236, 237, 238, 235, 237, 237, 238, 235, 235, 237, 236, 234, 237, 235, 235, 235, 236, 235, 237, 235, 236, 236, 237,
		235, 237, 235, 236, 236, 236, 236, 235, 235, 235, 234, 234], "coordinates": [(484, 539), (500, 539), (484, 555), (500, 555)]}
		self.spaces["nwc10"] = {"MaxOccupancy":1000, "PermanentSpace":False, "AverageConsumption":300, "AverageTemp":60, "ConsumptionOverTime":
		[178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 
		177, 178, 177, 177, 178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 
		178, 178, 177, 177, 177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176, 178, 178, 177, 178, 177, 178, 177, 177, 178, 178, 177, 177, 
		177, 178, 178, 177, 176, 177, 178, 178, 178, 177, 177, 176], "coordinates": []}
		self.spaces["nwc1008"] = {"MaxOccupancy":2, "PermanentSpace":True, "AverageConsumption":700, "AverageTemp":70, "ConsumptionOverTime":
		[174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173,
		174, 173, 174, 173, 174, 173, 174, 173, 174, 173, 174, 173], "coordinates": [(204, 509), (220, 509)]}
S = simulator()
S.timedSimulatedAnnealing(1000)