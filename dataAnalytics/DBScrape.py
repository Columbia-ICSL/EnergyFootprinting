import pymongo
import datetime

class DBScrape():
	def __init__(self):
		self.dbc=pymongo.MongoClient()
		return

	def registration_col1(self):
		self.registration_col1=self.dbc.db.registration_col1
		return list(self.registration_col1.find())

	def snapshots_col_appliances(self, start, end):
		self.snapshots_col_appliances=self.dbc.db.snapshots_col_appliances
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(self.snapshots_col_appliances.find(condition))

	def snapshots_col_rooms(self, start, end):
		self.snapshots_col_rooms=self.dbc.db.snapshots_col_rooms
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(self.snapshots_col_rooms.find(condition))

	def snapshots_col_users(self, start, end):
		print("got to db scrape")
		self.snapshots=self.dbc.db.snapshots_col_users
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(self.snapshots.find(condition))

	def todayCumulativeEnergy(self):
		self.todayCumulativeEnergy=self.dbc.db.todayCumulativeEnergy



db=DBScrape()