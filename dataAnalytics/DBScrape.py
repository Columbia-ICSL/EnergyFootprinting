import pymongo

class DBScrape():
	def __init__(self):
		self.dbc=pymongo.MongoClient()
		return

	def registration_col1(self):
		self.registration_col1=self.dbc.db.registration_col1
		print(list(self.registration_col1.find()))
		return list(self.registration_col1.find())

	def snapshots_col_appliances(self):
		self.snapshots_col_appliances=self.dbc.db.snapshots_col_appliances

	def snapshots_col_rooms(self):
		self.snapshots_col_rooms=self.dbc.db.snapshots_col_rooms

	def snapshots_col_users(self):
		self.snapshots_col_users=self.dbc.db.snapshots_col_users

	def todayCumulativeEnergy(self):
		self.todayCumulativeEnergy=self.dbc.db.todayCumulativeEnergy



db=DBScrape()