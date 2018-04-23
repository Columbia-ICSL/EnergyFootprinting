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
		self.locations = {}
		self.rewards = {}
		self.getUsers()

		#self.getUserLocations()
	

	def getUsers(self):
		#create a list of users from the database
		self.users = cloudserver.db.dumpUsers()
		print "Loaded " + str(len(self.users)) + " users"
		for user in self.users:
			if "name" not in user or "userID" not in user:
				continue
			self.userRecommendations[user["userID"]] = user["name"]
			self.rewards[user["userID"]] = user["balance"]
		print "Loaded user recommendations dictionary"
		print self.userRecommendations

	def loadBuildingParams(self):
		return

	def getUserLocations(self):
		self.locations = cloudserver.db.location_of_users
		return

	def returnRecs(self, user):
		balance = 0
		if user in self.rewards:
			balance = self.rewards[user]
		tempBalance = balance
		json_return={
            "location":"Location Name",
            "location_id":"locationIDString",
            "balance":balance,
            "tempBalance": tempBalance,
            "suggestions":[]
		}
		location = "outOfLab"
		if user in self.locations:
			location = self.locations[user]
		json_return["location_id"]=location
		json_return["location"]=cloudserver.db.RoomIdToName(location)
		ret = cloudserver.db._encode(json_return,False)
		return ret

	def bestRecommendations(self):
		return

	def make_suggestion_item(iType, iTitle, iBodyText, iReward, messageID, inotification=0, Others={}):
		Others.update({
            "type":iType,
            "title":iTitle,
            "body":iBodyText,
            "reward":iReward,
            "notification":inotification,
            "messageID":messageID
            })
		return Others












	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			self.getUserLocations()
			print "Interval"
