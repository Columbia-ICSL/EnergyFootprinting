import pymongo
import datetime
import time
import calendar
from bson import ObjectId

class DBMgr(object):
	def GetConfigValue(self,key):
		return self.config_col.find_one({"_id":key})["value"]
	def SetConfigValue(self,key,value):
		self.config_col.replace_one({"_id":key},{"value":value},True)

	def __init__(self):
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.config_col=self.dbc.db.config

		"""self.T=900
		self.dbc=pymongo.MongoClient()
		self.engcol=self.dbc.db.energy_logs
		#standardized energy consumption, by each appliance, (each incidence)
		#(room, timestamp, watts, type/description ...)
		self.poscol=self.dbc.db.position_logs
		#position log 
		#(user, roomID, timestamp)
		self.raw_data=self.dbc.db.raw_data_logs
		#any raw data document.

		self.stdcol=self.dbc.db.standardized_consumption_log_column
		#(room,#T,value, consumption=[?,?], occupants=[], responsibility=[?,?])
		#(#T = timestamp / 15min)
		# responsibility is inherited from last nonempty resp, if loc history is empty
		# consumption history is non-repetitively added from energy_logs

		self.room_meta=self.dbc.db.room_meta
		#(room, PULLcallbackURL, latestUpdate)"""

	def ReportEnergyValue(self, deviceID, value, raw_data):
		#get roomID from config database
		#save raw data to raw database
		#save latest value into tree (in memory)
		"maintenance tree's energy value"


	def ReportLocationAssociation(self,userID, roomID, raw_data):
		#save raw data
		#change the tree; 
			#add to new location, remove from old location. maintenance the tree from both leaf.
				#need to update: number_of_users in these nodes.			
		"maintenance each user's value"

	def SaveShot(self, any_additional_data):
		#transform the tree
		#save into database, with: timestamp, additional data
		"insert the tree into tree_collections"

if __name__ == "__main__":
	"a"
	#db=DBMgr()
	#db._TEST()