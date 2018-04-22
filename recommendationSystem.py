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
		self.getUsers()

	def getUsers(self):
		#create a list of users from the database
		self.users = cloudserver.db.dumpUsers()
		print "Loaded " + len(self.users) + " users"















	def startDaemon(self):
		t=Thread(target=self._loopCheckDatabase,args=())
		t.setDaemon(True)
		t.start()

	def _loopCheckDatabase(self):
		while True:
			time.sleep(self.checkInterval)
			print "Interval"
