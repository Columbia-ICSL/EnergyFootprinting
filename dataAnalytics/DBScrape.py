import pymongo
import datetime
###################
### NOTE: Peter screwed up big time and named everything self, which is basically
### the same damn thing as in the DBMgr.py! What an idiot
### If there are bugs from calling DBScrape.py, it probably stems from previously
### saving what are now called "snapshots" in the class methods below as self.something
###################
class DBScrape():
	def __init__(self):
		self.dbc=pymongo.MongoClient()
		return

	def registration_col1(self):
		registration=self.dbc.db.registration_col1
		return list(registration.find())

	def snapshots_col_appliances(self, start, end):
		snapshots=self.dbc.db.snapshots_col_appliances
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(snapshots.find(condition))

	def snapshots_col_rooms(self, start, end):
		snapshots=self.dbc.db.snapshots_col_rooms
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(snapshots.find(condition))

	def snapshots_col_users(self, start, end):
		snapshots=self.dbc.db.snapshots_col_users
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		return list(snapshots.find(condition))

	def snapshots_parameters(self):
		snapshots = self.dbc.db.snapshots_parameters
		condition = {

		}
		return list(snapshots.find(condition))
		

	def todayCumulativeEnergy(self):
		self.todayCumulativeEnergy=self.dbc.db.todayCumulativeEnergy



db=DBScrape()