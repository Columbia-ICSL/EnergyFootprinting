import pymongo
import datetime
import time
import calendar
import traceback
from bson import ObjectId
import json
import pprint
from threading import Thread

def add_log(msg,obj):
	print "Got log:"+msg
	print obj
	traceback.print_exc()
	pymongo.MongoClient().log_db.log.insert({
		"msg":msg,
		"obj":obj,
		"timestamp":datetime.datetime.utcnow()
		});
def dump_debug_log():
	return pprint.pformat(
		list(pymongo.MongoClient().log_db.log.find()),
	indent=2)
def dump_recent_raw_submission():
	return pprint.pformat(
		list(pymongo.MongoClient().db.raw_data.find().sort([("_log_timestamp", -1)]).limit(500)),
	indent=2)

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
	
	def _encode(self,data,isPretty):
		return json.dumps(data, sort_keys=True, indent=4)
	def __init__(self):
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.config_col=self.dbc.db.config
		self.UpdateConfigs()
		self.save_interval=60 #every minute

		self.people_in_space={}; "!!! should read snapshot"
		self.tree_of_space={}; "!!! should also read shapshot to get latest energy values?"
		#transpose array
		for room in self.ROOM_DEFINITION:
			self.tree_of_space[room["id"]]=room
			if not ("consumption"  in self.tree_of_space[room["id"]]):
				self.tree_of_space[room["id"]]["consumption"]={}
				#preserve pre-defined onstant consumptions

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

		t=Thread(target=self._loopSaveShot,args=())
		t.setDaemon(True)
		t.start()

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

	def updateTreeTotalCon(self,roomID):
		total_con=0
		for iter_devID in self.tree_of_space[roomID]["consumption"]:
			total_con+=self.tree_of_space[roomID]["consumption"][iter_devID]["value"]
		self.tree_of_space[roomID]["_sum_consumption"]=total_con

		self.tree_of_space[roomID]["_sum_consumption_including_children"]=total_con
		for c in self.tree_of_space[roomID]["children"]:
			if "_sum_consumption_including_children" in self.tree_of_space[c]:
				self.tree_of_space[roomID]["_sum_consumption_including_children"]+=self.tree_of_space[c]["_sum_consumption_including_children"]

		if "father" in self.tree_of_space[roomID]:
			self.updateTreeTotalCon(self.tree_of_space[roomID]["father"])

	def LogRawData(self,obj):
		obj["_log_timestamp"]=datetime.datetime.utcnow()
		self.raw_data.insert(obj)

	def ReportEnergyValue(self, deviceID, value, raw_data=None):
		"maintenance tree node's energy consumption item, and update a sum value"
		known_room=None
		try:
			device=self.ENERGYDEVICE_DEFINITION[deviceID]
			roomID=device["room"]
			known_room=roomID

			self.tree_of_space[roomID]["consumption"][deviceID]={
				"value":value,
				"type":device["type"]
			}
		except:
			add_log("failed to report energy value on device",{
				"known_room":known_room,
				"deviceID":deviceID,
				"value":value,
				"raw":raw_data
				})
			return
		
		try:
			self.updateTreeTotalCon(roomID)
		except:
			add_log("failed to calculate accumulate total consumption",{
				"known_room":known_room,
				"room_current_cons":self.tree_of_space[known_room]["consumption"],
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
		

	def ReportLocationAssociation(self,personID, roomID, raw_data=None):
		self.LogRawData({
			"type":"location_report",
			"roomID":roomID,
			"personID":personID,
			"raw":raw_data
			})
		"!!! if roomID='' means he's out of tracking scope. maybe set to CUROOT?? "
		if not (roomID in self.tree_of_space):
			add_log("illegitimate roomID",{
					"p":personID,
					"r":roomID,
					"d":raw_data
				})
			return

		try:
			if personID in self.people_in_space:
				oldS=self.people_in_space[personID]
				if(roomID==oldS): 
					return;
				if self.tree_of_space[oldS]["occupants"]["type"]=="auto":
					try:	
						self.tree_of_space[oldS]["occupants"]["ids"].remove(personID)
						self.updateTreeOccNum(oldS)
					except:
						add_log("error while removing ID and updateTreeOccNum",oldS)
						print "error while removing ID and updateTreeOccNum"+oldS
						print self.tree_of_space[oldS]

			self.people_in_space[personID]=roomID
			if self.tree_of_space[roomID]["occupants"]["type"]=="auto": 
				try:	
					self.tree_of_space[roomID]["occupants"]["ids"]+=[personID]
					self.updateTreeOccNum(roomID)
				except:
					add_log("error while adding ID and updateTreeOccNum",roomID)
					print "error while adding ID and updateTreeOccNum"+roomID
					print self.tree_of_space[roomID]

			self.recordEvent(personID,"locationChange",roomID)

		except:
			add_log("error while maintaining people_in_space[personID]. ",{
				"personID":personID,
				"roomID":roomID
				})

		#"maintenance each user's value"
		"maintanence involves too much space and other people; shouldn't do it here. moved to snapshot section"

	def SaveShot(self, any_additional_data=None):
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
				"!!! should also consider the eng cons. of parent nodes?"
				roomID=self.people_in_space[personID]
				e_value=-1
				if "_sum_consumption_including_children" in self.tree_of_space[roomID]:
					e_value=self.tree_of_space[roomID]["_sum_consumption_including_children"] / self.tree_of_space[roomID]["occupants"]["number"]
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


		ret={"tree":self.tree_of_space, "personal":personal_consumption }
		#if self.tree_of_space[roomID]["occupants"]["type"]=="auto":
		return self._encode(ret,True)

		"3. possible accumulation at different tier?? like every 600 seconds?"

	def _loopSaveShot(self):
		while True:
			self.SaveShot()
			time.sleep(self.save_interval)


	def QueryRoom(self,room,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"data."+room:1,"timestamp":1}
		iterator = self.tree_snapshot_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			if room in shot['data']:
				item=shot["data"][room]
				item["timestamp"]=shot["timestamp"]
				result+=[item]
		return self._encode(result,True)
		#return '{"result":"Query not finished yet."}'

	def QueryPerson(self,person,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"data."+person:1,"timestamp":1}
		iterator = self.personal_snapshot_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			if person in shot["data"]:
				item=shot["data"][person]
				item["timestamp"]=shot["timestamp"]
				result+=[item]
		
		return self._encode(result,True)

if __name__ == "__main__":
	dbm=DBMgr()
	dbm._TEST()

