import cloudserver
from threading import Thread
import time
import datetime
class suggestionsEngine:
	moveLimit = 3
	checkInterval = 30 #1 minute
	moveUsers = []
	sortedRoomList = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c"]
	sortedRoomOccupancy = [0] * len(sortedRoomList)
	roomOccupancySnapshot = ""
	changeScheduleUsers = []
	turnOffApplianceUsers = {}
	synchronizeApplianceUsers = []
	def moveSuggestion(self):
		list_of_rooms = cloudserver.db.CurrentOccupancy()
		users = []
		self.roomOccupancySnapshot = ""
		for roomID in list_of_rooms:
			userList = list_of_rooms[roomID]
			occupancy = len(userList)
			index = self.sortedRoomList.index(roomID)
			self.sortedRoomOccupancy[index] = occupancy
			if (len(userList) < self.moveLimit):
				users.extend(userList)
		for i in range(len(self.sortedRoomOccupancy)):
			self.roomOccupancySnapshot += str(self.sortedRoomOccupancy[i])
			self.roomOccupancySnapshot += ";"
		return users

############## TODO #################
	def changeScheduleSuggestion(self):
		users = []
		return users
	def turnOffApplianceSuggestion(self):
		personalUsage = CurrentApplianceUsage(5)
		users = {}
		for person in personalUsage:
			users[person] = personalUsage[person]
		return users
	def synchronizeApplianceScheduleSuggestion(self):
		users = []
		return users
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