import cloudserver
from threading import Thread
import time
import datetime
class suggestionsEngine:
	moveLimit = 3
	checkInterval = 60 #1 minute
	moveUsers = []
	roomOccupancySnapshot = ""
	changeScheduleUsers = []
	turnOffApplianceUsers = []
	synchronizeApplianceUsers = []
	def moveSuggestion(self):
		list_of_rooms = cloudserver.db.CurrentOccupancy()
		users = []
		roomOccupancySnapshot = ""
		for roomID in list_of_rooms:
			userList = list_of_rooms[roomID]["users"]
			occupancy = len(userList)
			roomOccupancySnapshot += str(roomID)
			roomOccupancySnapshot += " "
			roomOccupancySnapshot += str(occupancy)
			roomOccupancySnapshot += ";"
			if (len(userList) < moveLimit):
				users.extend(userList)
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