import cloudserver
from threading import Thread
import time
import datetime
import csv

PUBLIC_SPACE = 0
BURKE_LAB = 1
TEHARANI_LAB = 2
JIANG_LAB = 3
SAJDA_LAB = 4
DANINO_LAB = 5
OFFICE_SPACE = 0
STUDENT_WORK_SPACE = 1
GENERAL_SPACE = 2
WINDOWED = True
NOT_WINDOWED = False
ACTIONABLE = True
NOT_ACTIONABLE = False
DUTY_CYCLE = True
NO_DUTY_CYCLE = False
class suggestionsEngine:
	moveLimit = 3
	checkInterval = 30 #1 minute
	moveUsers = {}
	roomOccupancySnapshot = ""
	changeScheduleUsers = {}
	turnOffApplianceUsers = {}
	synchronizeApplianceUsers = {}
	phantomApplianceUsers = {}
	lastDayCheckUsers = None
	lastDayCheckAppliances = None
	def moveSuggestionHelper(self, roomOrigin, roomDest, messageID, Others={}):
		Others.update({
			"roomOrigin": roomOrigin,
			"roomDest": roomDest,
			"messageID":messageID
			})
		return Others

	def moveSuggestion(self):
		users = {}
		list_of_rooms = cloudserver.db._getShotRooms()
		lab_maximum = [(0,0), (0,0), (0,0), (0,0), (0,0), (0,0)]
		for roomID in list_of_rooms:
			userList = list_of_rooms[roomID]["users"]
			occupancy = len(userList)
			labDefinition = list_of_rooms[roomID]["lab"]
			cur_max = lab_maximum[labDefinition][1]
			if (occupancy >= cur_max and (list_of_rooms[roomID]["space"] == STUDENT_WORK_SPACE)):
				lab_maximum[labDefinition] = (roomID, occupancy)
		for roomID in list_of_rooms:
			userList = list_of_rooms[roomID]["users"]
			occupancy = len(userList)
			labDefinition = list_of_rooms[roomID]["lab"]
			roomDest = lab_maximum[labDefinition][0]
			if (occupancy > 0 and occupancy < self.moveLimit):
				if (roomID == roomDest):
					continue
				if (list_of_rooms[roomDest]["space"] == list_of_rooms[roomID]["space"]):
					for user in userList:
						messageID = "{0}|{1}|{2}".format("move", str(user), str(roomDest))
						users[user] = self.moveSuggestionHelper(roomID, roomDest, messageID)
		return users





		#list_of_rooms = cloudserver.db.CurrentOccupancy()
		#users = []
		#self.roomOccupancySnapshot = ""
		#for roomID in list_of_rooms:
		#	userList = list_of_rooms[roomID]
		#	occupancy = len(userList)
		#	index = self.sortedRoomList.index(roomID)
		#	self.sortedRoomOccupancy[index] = occupancy
		#	if (len(userList) < self.moveLimit):
		#		users.extend(userList)
		#for i in range(len(self.sortedRoomOccupancy)):
		#	self.roomOccupancySnapshot += str(self.sortedRoomOccupancy[i])
		#	self.roomOccupancySnapshot += ";"
		#return users

############## TODO #################
	def changeScheduleSuggestion(self):
		tmp = self.changeScheduleUsers
		now = datetime.datetime.now()
		if ((self.lastDayCheckUsers == None) or ((self.lastDayCheckUsers.day != now.day) and (now.hour >= 2) and (now.hour < 5))):
			self.lastDayCheckUsers = now
			users = {}
			startAvg = [0, 0, 0, 0, 0]
			endAvg = [0, 0, 0, 0, 0]
			nowTime = datetime.datetime.now().replace(hour=4, minute=0)
			print("4AM today: " + str(nowTime))
			curtime = int(time.mktime(nowTime.timetuple()))
			dict_users = cloudserver.db.BinUsersLocHistory(curtime-86400, curtime)
			numUsers = [0, 0, 0, 0, 0]
			userDict = {}

			#with open('changeSchedule.csv', 'w') as csvfile:
			#	writer = csv.writer(csvfile, delimiter=' ',
			#		quotechar='|', quoting=csv.QUOTE_MINIMAL)
			#	user_list = []
#
#				user_list.append(0)
#				return_bins = dict_users[dict_users.keys()[0]]
#				for bin_start in sorted(return_bins.keys()):
#					user_list.append(bin_start)
#				writer.writerow(user_list)
#				user_list = []
#				for user_id in dict_users:
#					user_list = []
#					userName = cloudserver.db.userIDLookup(user_id)
#					user_list.append(userName)
#					return_bins = dict_users[user_id]
#					for bin_start in sorted(return_bins.keys()):
#						BIN_ST = return_bins[bin_start]
#						if (BIN_ST["value"] == None):
#							user_list.append(0)
#						else:
#							user_list.append(BIN_ST["value"])
#					writer.writerow(user_list)

			for user_id in dict_users:
				userStart = 0
				userEnd = 0
				userName = cloudserver.db.userIDLookup(user_id)
				if userName == None:
					continue
				attributes = cloudserver.db.getAttributes(userName, False)#Burke, Teherani, Jiang, Sajda, Danino
				lab = attributes["lab"]-1
				numUsers[lab] += 1
				return_bins = dict_users[user_id]
				for bin_start in sorted(return_bins.keys()):
					BIN_ST = return_bins[bin_start]
					if ((userStart == 0) and (BIN_ST["location"] is not None)):
						userStart = bin_start
						userEnd = bin_start
					if (BIN_ST["location"] is not None):
						userEnd = bin_start
				startAvg[lab] += userStart
				endAvg[lab] += userEnd
				userDict[user_id] = (userStart, userEnd, lab)
				print("{0} {1}-{2}".format(user_id, str(datetime.datetime.fromtimestamp(userStart)), str(datetime.datetime.fromtimestamp(userEnd))))
			for labName in xrange(len(startAvg)):
				if (numUsers[labName] == 0):
					numUsers[labName] = 1
				startAvg[labName] = float(startAvg[labName]/numUsers[labName])
				endAvg[labName] = float(endAvg[labName]/numUsers[labName])
				labStrings = ["Burke", "Teherani", "Jiang", "Sajda", "Danino"]
				print("avg: ------------------------ {0} {1} lab {2}".format(str(datetime.datetime.fromtimestamp(startAvg[labName])), str(datetime.datetime.fromtimestamp(endAvg[labName])), str(labStrings[labName])))
			for userRange in userDict:
				labNum = userDict[userRange][2]
				if ((userDict[userRange][0] > startAvg[labNum]) and (userDict[userRange][1] > endAvg[labNum])):
					print("suggestion: {0} {1}".format(userRange, "earlier"))
					users[userRange] = ("earlier", startAvg[labNum], endAvg[labNum])
				if ((userDict[userRange][0] < startAvg[labNum]) and (userDict[userRange][1] < endAvg[labNum])):
					print("suggestion: {0} {1}".format(userRange, "later"))
					users[userRange] = ("later", startAvg[labNum], endAvg[labNum])
			tmp = users
		#print("{0}".format(self.lastDayCheckUsers))
		return tmp

	def phantomApplianceSuggestion(self):
		return cloudserver.db.phantomApplianceUsage(10*60, 50) #delayTime, power limit

	def turnOffApplianceSuggestion(self):
		personalUsage = cloudserver.db.CurrentApplianceUsage(5)
		#users = {}
		#for person in personalUsage:
			#for appliance in personalUsage[person]:
			#	messageID = "{0}|{1}|{2}".format("turnoff", str(person), appliance["id"])
		#	users[person] = personalUsage[person]
		return personalUsage

	def synchronizeApplianceScheduleSuggestion(self):
		tmp = self.synchronizeApplianceScheduleSuggestion
		now = datetime.datetime.now()
		if ((self.lastDayCheckAppliances == None) or ((self.lastDayCheckAppliances.day != now.day) and (now.hour >= 2) and (now.hour < 5))):
			self.lastDayCheckAppliances = now
			users = []
		print("{0}".format(self.lastDayCheckAppliances))
		return tmp
#######################################


	def __init__(self):
		self.startDaemon()

	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			self.moveUsers = {} #self.moveSuggestion()
			self.changeScheduleUsers = {} #self.changeScheduleSuggestion()
			self.phantomApplianceUsers = {} #self.phantomApplianceSuggestion()
			self.turnOffApplianceUsers = {} #self.turnOffApplianceSuggestion()
			self.synchronizeApplianceUsers = {} #self.synchronizeApplianceScheduleSuggestion()
			#print("Suggestions Generated: #users receiving suggestion= move:{0} changeSchedule:{1} turnOff:{2} sync:{3}".format(len(self.moveUsers.keys()), len(self.changeScheduleUsers()), len(self.turnOffApplianceUsers.keys()), len(self.synchronizeApplianceUsers())))




