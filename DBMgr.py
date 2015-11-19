import pymongo
import datetime
import time
import calendar
from bson import ObjectId

def add_log(msg,obj):
	pymongo.MongoClient().log_db.log.insert({
		"msg":msg,
		"obj":obj,
		"timestamp":datetime.datetime.utcnow()
		});

class DBMgr(object):
	def _GetConfigValue(self,key):
		try:
			ret=self.config_col.find_one({"_id":key})
			return ret["value"]
		except:
			return None

	def _SetConfigValue(self,key,value):
		self.config_col.replace_one({"_id":key},{"value":value},True)

	def UpdateConfigs(self):
		self.ROOM_DEFINITION=self._GetConfigValue("ROOM_DEFINITION")
		self.ENERGYDEVICE_DEFINITION=self._GetConfigValue("ENERGYDEVICE_DEFINITION")
		

	def __init__(self):
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.config_col=self.dbc.db.config
		self.UpdateConfigs()

		self.people_in_space={}; "!!! should read snapshot"
		self.tree_of_space={}; "!!! should also read shapshot to get latest energy values?"
		#transpose array
		for room in self.ROOM_DEFINITION:
			self.tree_of_space[room["id"]]=room
		#maintenance of father
		for room in self.ROOM_DEFINITION:
			for c in room["children"]:
					self.tree_of_space[c]["father"]=room["id"]

		self.raw_data=self.dbc.db.raw_data
		#any raw data document.

		self.snapshot_col=self.dbc.db.snapshot_col
		#snapshot every x seconds, for the tree

	def updateTreeOccNum(self,node_id):#update till root, or encounter a non-auto index
		if self.tree_of_space[node_id]["occupants"]["type"]!="auto":
			return
		#only update auto occupant #
		try:
			num_this_layer=len(self.tree_of_space[node_id]["occupants"]["ids"])
			num_lower_layer=0
			for c in self.tree_of_space[node_id]["children"]:
				num_lower_layer+=self.tree_of_space[c]["occupants"]["number"]

			self.tree_of_space[node_id]["occupants"]["number"]=num_lower_layer+num_this_layer
		except:
			add_log("error while calculating #occ node",node_id)
			return
		
		try:
			father_id=self.tree_of_space[node_id]["father"]
			self.updateTreeOccNum(father_id)
		except:
			add_log("error while tracing father at node",node_id)
			return
		
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
		#save into database, with: timestamp, additional data
		"insert the tree into snapshot_col"

#if __name__ == "__main__":
#	db=DBMgr()
#	db._TEST()