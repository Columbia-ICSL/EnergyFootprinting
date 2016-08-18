import cloudserver
from threading import Thread
import time
import datetime
class suggestionsEngine:
	moveLimit = 3
	checkInterval = 60 #1 minute
	moveUsers = []
	sortedRoomList = ["nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g", "nwc1008"]
	sortedRoomOccupancy = [0] * len(sortedRoomOccupancy)
	roomOccupancySnapshot = ""
	changeScheduleUsers = []
	turnOffApplianceUsers = []
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
		for i in range(len(sortedRoomOccupancy)):
			self.roomOccupancySnapshot += str(self.sortedRoomOccupancy[i])
			self.roomOccupancySnapshot += ";"
		return users

############## TODO #################
	def changeScheduleSuggestion(self):
		users = []
		return users
	def turnOffApplianceSuggestion(self):
		users = []
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