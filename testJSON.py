SQFT = 10000
numPeople = SQFT/250
numDevices = numPeople*2
numSpaces = SQFT/500-1

import copy
IDs = []
for i in range(numPeople):
	newID = "P" + str(i)
	IDs.append(newID)
D = []
for i in range(numDevices):
	newDevice = "D" + str(i)
	D.append(newDevice)
S = []
S.append("outOfLab")
for i in range(numSpaces):
	newSpace = "S" + str(i)
	S.append(newSpace)
NS = []
realS = copy.copy(S)

P = []
PO = []

import datetime
import random

testshot = {}

appDictionary = {}

for app in D:
	parameters = {}
	space1 = random.randint(0, numSpaces)
	space2 = random.randint(0, numSpaces)
	parameters["rooms"] = ["S" + str(space1), "S" + str(space2)]
	r = random.uniform(0, 1)
	if r < 0.5:
		parameters["type"] = "Electric"
		P.append(app)
		PO.append("P" + str(random.randint(0,numPeople)))
	elif r >= 0.5 and r < 0.75:
		parameters["type"] = "Lights"
	elif r >= 0.75:
		parameters["type"] = "HVAC"
	parameters["value"] = random.uniform(0, 10000)
	appDictionary[app] = parameters

testshot["data"] = appDictionary
testshot["timestamp"] = datetime.datetime(2018, 6, 21)

print(testshot)

testUserShot = {}
userDictionary = {}

for user in IDs:
	parameters = {}
	parameters["consumptions"] = []
	parameters["location"] = "S" + str(random.randint(0,numSpaces))
	parameters["value"] = random.uniform(0, 3000)
	userDictionary[user] = parameters
testUserShot["data"] = userDictionary
testUserShot["timestamp"] = datetime.datetime(2018, 6, 21)

print(testUserShot)


