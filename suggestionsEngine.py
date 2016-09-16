import cloudserver
from threading import Thread
import time
import datetime

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
	sortedRoomList = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c", "10F_hallway", "DaninoWetLab"]
	sortedRoomOccupancy = [0] * len(sortedRoomList)
	roomOccupancySnapshot = ""
	changeScheduleUsers = []
	turnOffApplianceUsers = {}
	synchronizeApplianceUsers = []
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
		tmp = self.synchronizeApplianceUsers
		now = datetime.datetime.now()
		if ((self.lastDayCheckUsers == None) or ((self.lastDayCheckUsers.day != now.day) and (now.hour >= 2) and (now.hour < 5))):
			self.lastDayCheckUsers = now
			users = []
			userBins = cloudserver.db.BinUsersLocHistory()
			for userBin in userBins:
				for binNumber in userBins[userBin]:
					
		print("{0}".format(self.lastDayCheckUsers))
		return tmp

	def turnOffApplianceSuggestion(self):
		personalUsage = cloudserver.db.CurrentApplianceUsage(5)
		users = {}
		for person in personalUsage:
			#for appliance in personalUsage[person]:
			#	messageID = "{0}|{1}|{2}".format("turnoff", str(person), appliance["id"])
			users[person] = personalUsage[person]
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
			self.moveUsers = self.moveSuggestion()
			self.changeScheduleUsers = self.changeScheduleSuggestion()
			self.turnOffApplianceUsers = self.turnOffApplianceSuggestion()
			self.synchronizeApplianceUsers = self.synchronizeApplianceScheduleSuggestion()
			#print("Suggestions Generated: #users receiving suggestion= move:{0} changeSchedule:{1} turnOff:{2} sync:{3}".format(len(self.moveUsers.keys()), len(self.changeScheduleUsers()), len(self.turnOffApplianceUsers.keys()), len(self.synchronizeApplianceUsers())))




