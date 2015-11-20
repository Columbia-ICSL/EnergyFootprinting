import pymongo
import datetime
import time
import calendar
from bson import ObjectId
import json

def add_log(msg,obj):
	print "Got log:"+msg
	print obj
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
			self.tree_of_space[room["id"]]["consumption"]={}
		#maintenance of father
		for room in self.ROOM_DEFINITION:
			for c in room["children"]:
					self.tree_of_space[c]["father"]=room["id"]


		self.raw_data=self.dbc.db.raw_data
		#any raw data document.

		self.tree_snapshot_col=self.dbc.db.tree_snapshot_col
		self.personal_snapshot_col=self.dbc.db.personal_snapshot_col
		#snapshot every x seconds, for the tree


		self.events_col=self.dbc.db.events_col
		#person ID events, like location change

	def _TEST(self):
		print "TEST"
		self.tree_of_space["nwc1003b"]["occupants"]["ids"]=["xc2340"]
		self.updateTreeOccNum("nwc1003b")
		#print json.dumps(self.tree_of_space,indent=2, separators=(',', ': '))
		#self.tree_of_space["nwc1003b"]["occupants"]["ids"]=[]
		#self.updateTreeOccNum("nwc1003b")
		print self.tree_of_space["nwc10"]["occupants"]

	def recordEvent(self, personID, etype, data):
		self.events_col.insert({
			"personID":personID,
			"type":etype,
			"data":data
			})

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
		
		self.stdcol=self.dbc.db.standardized_consumption_log_column
		#(room,#T,value, consumption=[?,?], occupants=[], responsibility=[?,?])
		#(#T = timestamp / 15min)
		# responsibility is inherited from last nonempty resp, if loc history is empty
		# consumption history is non-repetitively added from energy_logs

		self.room_meta=self.dbc.db.room_meta
		#(room, PULLcallbackURL, latestUpdate)"""
	def LogRawData(self,obj):
		obj["_timestamp"]=datetime.datetime.utcnow()
		self.raw_data.insert(obj)

	def ReportEnergyValue(self, deviceID, value, raw_data):
		"maintenance tree node's energy consumption item, and update a sum value"
		known_room=None
		try:
			device=self.ENERGYDEVICE_DEFINITION["deviceID"]
			roomID=device["room"]
			self.tree_of_space[roomID]["consumption"][deviceID]={
				"value":value,
				"type":device["type"]
			}
			total_con=0
			for iter_devID in self.tree_of_space[roomID]["consumption"]:
				total_con+=self.tree_of_space[roomID]["consumption"][iter_devID]["value"]
			self.tree_of_space[roomID]["_sum_consumption"]=total_con

			known_room=roomID
		except:
			add_log("failed to report energy value on device",{
				"deviceID":deviceID,
				"value":value,
				"raw":raw_data
				})

		self.LogRawData({
			"type":"energy_report",
			"roomID":known_room,
			"deviceID":deviceID,
			"value":value,
			"raw":raw_data
			})
		

	def ReportLocationAssociation(self,personID, roomID, raw_data):
		self.LogRawData({
			"type":"location_report",
			"roomID":roomID,
			"personID":personID,
			"raw":raw_data
			})
		"!!! if roomID='' means he's out of tracking scope. maybe set to CUROOT?? "

		try:
			if personID in self.people_in_space:
				oldS=self.people_in_space[personID]
				if(roomID==oldS): 
					return;
				self.tree_of_space[oldS]["occupants"].remove(personID)
				self.updateTreeOccNum(oldS)

			self.people_in_space[personID]=roomID
			self.tree_of_space[roomID]["occupants"]+=[personID]
			self.updateTreeOccNum(roomID)

			self.recordEvent(personID,"locationChange",roomID)

		except:
			add_log("error when maintaining ids list",{
				"personID":personID,
				"roomID":roomID
				})

		#"maintenance each user's value"
		"maintanence involves too much space and other people; shouldn't do it here. moved to snapshot section"

	def SaveShot(self, any_additional_data):
		#save into database, with: timestamp, additional data
		"1. insert the tree into snapshot_col"
		self.tree_snapshot_col.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":self.tree_of_space
			})
		#snapshot every x seconds, for the tree

		"2. record the people's consumption too"

		personal_consumption={}
		#for space_id in self.tree_of_space:
		for personID in self.people_in_space:
			try:
				roomID=people_in_space[personID]
				e_value=-1
				if "_sum_consumption" in self.tree_of_space[roomID]:
					e_value=self.tree_of_space[roomID]["_sum_consumption"] / self.tree_of_space[roomID]["occupants"]["number"]
				personal_consumption[personID]={
					"value":e_value,
					"roomID":roomID
				}
			except:
				add_log("fail to trace person's consumption; id:",personID)
			
		self.personal_snapshot_col.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":personal_consumption
			})


		#if self.tree_of_space[roomID]["occupants"]["type"]=="auto":



		"3. possible accumulation at different tier?? like every 600 seconds?"

if __name__ == "__main__":
	dbm=DBMgr()
	dbm._TEST()