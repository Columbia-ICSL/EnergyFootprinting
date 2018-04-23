import cloudserver
from threading import Thread
import time
import datetime


class recommenderSystem:
	def __init__(self):
		self.setup()
		self.startDaemon()

	def setup(self):
		self.checkInterval = 30
		self.users = None
		self.userRecommendations = {}
		self.getUsers()
	

	def getUsers(self):
		#create a list of users from the database
		self.users = cloudserver.db.dumpUsers()
		print "Loaded " + str(len(self.users)) + " users"
		for user in self.users:
			self.userRecommendations[user["userID"]] = user["name"]
		print "Loaded user recommendations dictionary"
		print self.userRecommendations

	def loadBuildingParams(self):
		return

	def getUserLocations(self):
		return

	def returnRecs(self, user):
		return

	def bestRecommendations(self):
		return














	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			print "Interval"
