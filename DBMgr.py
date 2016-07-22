import pymongo
import datetime
import time
import calendar
import traceback
from bson import ObjectId
import json
import pprint
import copy
from threading import Thread
import sys


class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            #return obj.isoformat()
            utc_seconds = calendar.timegm(obj.utctimetuple())
            return utc_seconds
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return super(MongoJsonEncoder, self).default(obj)


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
		self.save_interval=60 #every minute
		"!!! should read database to get 60..."

	def _encode(self,data,isPretty):
		return MongoJsonEncoder().encode(data)
	def __init__(self):
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()

		db1 = self.dbc.test_database
		coll1 = db1.test_collection

		self.config_col=self.dbc.db.config
		#metadata col

		self.raw_data=self.dbc.db.raw_data
		#any raw data document.

		self.tree_snapshot_col=self.dbc.db.tree_snapshot_col
		self.personal_snapshot_col=self.dbc.db.personal_snapshot_col
		#snapshot every x seconds, for the tree
		self.events_col=self.dbc.db.events_col
		#person ID events, like location change
		self._latestSuccessShot=0

		self.UpdateConfigs()

		self.tree_of_space={}; #transpose array
		for room in self.ROOM_DEFINITION:
			self.tree_of_space[room["id"]]=room
			if not ("consumption"  in self.tree_of_space[room["id"]]):
				self.tree_of_space[room["id"]]["consumption"]={}
			else:
				consumption=0
				for con_id in room["consumption"]:
					consumption+=room["consumption"][con_id]["value"]
				self.tree_of_space[room["id"]]["_sum_consumption"]=consumption
				#preserve pre-defined onstant consumption
				#calc _sum_consumption 

		#maintenance of father
		for room in self.ROOM_DEFINITION:
			for c in room["children"]:
					self.tree_of_space[c]["father"]=room["id"]

		"!!! should read shapshot to get latest energy values?"
		latest_snapshot=self.tree_snapshot_col.find_one(sort=[("timestamp", pymongo.DESCENDING)]);
		latest_snapshot=latest_snapshot["data"]
		for roomID in latest_snapshot:
			if self.tree_of_space[roomID]["consumption"]=={}:
				for deviceID in latest_snapshot[roomID]["consumption"]:
					if deviceID in self.ENERGYDEVICE_DEFINITION:
						self.tree_of_space[roomID]["consumption"][deviceID]=latest_snapshot[roomID]["consumption"][deviceID]
				try:
					self.tree_of_space[roomID]["_sum_consumption"]=latest_snapshot[roomID]["_sum_consumption"]
					self.tree_of_space[roomID]["_sum_consumption_including_children"]=latest_snapshot[roomID]["_sum_consumption_including_children"]
				except:
					add_log("warning: initialize error when copying old snapshot room consumption",roomID)
			#if self.tree_of_space[roomID]["occupants"]["type"]=="auto":
			#	try:
			#		self.tree_of_space[roomID]["occupants"]["ids"]=latest_snapshot[roomID]["occupants"]["ids"]
			#		self.tree_of_space[roomID]["occupants"]["number"]=latest_snapshot[roomID]["occupants"]["number"]
			#	except:
			#		add_log("warning: initialize error when copying old snapshot ids and #",roomID)
		
		self.people_in_space={}; "!!! should read snapshot"
		
		latest_snapshot=self.personal_snapshot_col.find_one(sort=[("timestamp", pymongo.DESCENDING)]);
		latest_snapshot=latest_snapshot["data"]
		for personID in latest_snapshot:
			if "roomID" in latest_snapshot[personID]:
				roomID=latest_snapshot[personID]["roomID"]
				#self.people_in_space[personID]=roomID #conflict to automatic assignment
				print "recovery person in room:"+personID+";"+roomID
				self.ReportLocationAssociation(personID,roomID,{"type":"recovery","rawSnap":latest_snapshot})
				#if self.tree_of_space[roomID]["occupants"]["type"] == 'auto':
				#	self.tree_of_space[roomID]["occupants"]["ids"]+=[personID]
					#self.tree_of_space[roomID]["occupants"]["number"]=len(...) #updateTreeOCcNum does that

		"try initialize _sum_consumption_including_children, to avoid empty entries"
		for roomID in self.tree_of_space:
			self.updateTreeTotalCon(roomID)

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
			"data":data,
			"timestamp":datetime.datetime.utcnow()
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
		
		try:
			if personID in self.people_in_space:
				oldS=self.people_in_space[personID]
				if(roomID==oldS): 
					return;
				if oldS!='false':
					if self.tree_of_space[oldS]["occupants"]["type"]=="auto":
						try:
							self.tree_of_space[oldS]["occupants"]["ids"].remove(personID)
							self.updateTreeOccNum(oldS)
						except:
							add_log("error while removing ID and updateTreeOccNum",oldS)
							print "error while removing ID and updateTreeOccNum"+oldS
							print self.tree_of_space[oldS]
		except:
			add_log("error while delete old spaceID. ",{
				"personID":personID,
				"roomID":roomID,
				"oldS":self.people_in_space[personID]
				})

		try:
			if not (roomID in self.tree_of_space):
				"if no legitimate roomID, then he's out of tracking. remove from tree."
				self.people_in_space[personID]='false'
				self.recordEvent(personID,"locationChange",False)
				return

			self.people_in_space[personID]=roomID
			if self.tree_of_space[roomID]["occupants"]["type"]=="auto": 
				try:	
					if personID not in self.tree_of_space[roomID]["occupants"]["ids"]:
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

		"people change; should we update now?"
		self.OptionalSaveShot();

	def OptionalSaveShot(self):
		"minimum interval: 10s; in lieu with regular snapshotting"
		if self._latestSuccessShot< self._now() -10 :
			self.SaveShot();

	def _getShotTree(self, concise=True):
		concise_tree=copy.deepcopy(self.tree_of_space)
		if concise:
			for id in concise_tree:
				for key in ["name","children","father","id"]:
					if key in concise_tree[id]:
						del concise_tree[id][key]
			for id in concise_tree:
				for cid in concise_tree[id]["consumption"]:
					concise_cons={
						"type":concise_tree[id]["consumption"][cid]["type"],
						"value":concise_tree[id]["consumption"][cid]["value"]
					}
					concise_tree[id]["consumption"][cid]=concise_cons
		return concise_tree

	def _getShotPersonal(self):
		personal_consumption={}
		#for space_id in self.tree_of_space:
		for personID in self.people_in_space:
			try:

				roomID=self.people_in_space[personID]
				if roomID=='false':
					personal_consumption[personID]={
						"value":0,
						"roomID":'unknown',
						"all_items":{}, #may not be necessary
						"type_aggregate":{}
					}
					continue;

				e_value=0
				if "_sum_consumption_including_children" in self.tree_of_space[roomID]:
					e_value=self.tree_of_space[roomID]["_sum_consumption_including_children"] / self.tree_of_space[roomID]["occupants"]["number"]
				all_items={}
				for iid in self.tree_of_space[roomID]["consumption"]:
					con_item=self.tree_of_space[roomID]["consumption"][iid]
					all_items[iid]={
						"weight":1.0/self.tree_of_space[roomID]["occupants"]["number"],
						"value":con_item["value"],
						"type":con_item["type"]
					}

				"TODO: should also consider the eng cons. of parent nodes. Use _sum_consumption instead of _sum_consumption_including_children."
				currID=roomID
				try:
					while "father" in self.tree_of_space[currID]:
						currID=self.tree_of_space[currID]["father"]
						consumption=self.tree_of_space[currID]["consumption"]
						occupants=1.0*self.tree_of_space[currID]["occupants"]["number"]
						e_value+= self.tree_of_space[currID]["_sum_consumption"] / occupants
						for iid in consumption:
							all_items[iid]={
								"weight":1.0/occupants,
								"value":consumption[iid]["value"],
								"type":consumption[iid]["type"]
							}
						
				except:
					add_log("error when tracing consumption through parent",{
						"me":personID,
						"at":roomID,
						"traced until":currID
						})

				agg_type={}
				for iid in all_items:
					item=all_items[iid]
					itype=item["type"]
					if not (itype in agg_type):
						agg_type[itype]={
							"ids":[],
							"value":0
						}
					
					agg_type[itype]["ids"]+=[iid]
					agg_type[itype]["value"]+=item["value"]*item["weight"]
				

				personal_consumption[personID]={
					"value":e_value,
					"roomID":roomID,
					"all_items":all_items, #may not be necessary
					"type_aggregate":agg_type
				}
			except:
				add_log("fail to trace person's consumption; id:",personID)
		return personal_consumption

	def SaveShot(self, any_additional_data=None):
		#save into database, with: timestamp, additional data
		"1. insert the tree into snapshot_col; remove some"
		concise_tree=self._getShotTree()
		self.tree_snapshot_col.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":concise_tree
			})
		#snapshot every x seconds, for the tree

		"2. record the people's consumption too"
		personal_consumption=self._getShotPersonal()
			
		self.personal_snapshot_col.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":personal_consumption
			})


		ret={"concise_tree":concise_tree, "personal":personal_consumption }
		#if self.tree_of_space[roomID]["occupants"]["type"]=="auto":
		return self._encode(ret,True)

		"2. TODO: maintain last entrance list of all rooms; check all occupants.number==0 rooms, make the last person liable."
		"3. possible accumulation at different tier?? like every 600 seconds?"

		self._latestSuccessShot=self._now();

	def _now(self):
		return calendar.timegm(datetime.datetime.utcnow().utctimetuple())
	def _loopSaveShot(self):
		while True:
			time.sleep(self.save_interval)
			self.SaveShot()

	def ShowRealtime(self, person=None, concise=True):
		#save into database, with: timestamp, additional data
		ret={
			"timestamp":self._now()
		}
		if person and person in self.people_in_space:
			d=self._getShotPersonal()
			ret["personal"]=d[person]
		else:
			ret["tree"]=self._getShotTree(concise)
			ret["locations"]=self.people_in_space
		return self._encode(ret,False)

	def QueryRoom(self,room,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"data."+room:1,"timestamp":1,"_id":0}
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
		projection = {"data."+person:1,"timestamp":1,"_id":0}
		iterator = self.personal_snapshot_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			if person in shot["data"]:
				item=shot["data"][person]
				item["timestamp"]=shot["timestamp"]
				result+=[item]
		
		return self._encode(result,True)


	def QueryPersonMulti(self,people,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"timestamp":1,"_id":0}
		for person in people:
			projection["data."+person]=1

		iterator = self.personal_snapshot_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			for personID in shot["data"]:
				#purge data
				try:
					shot["data"][personID]={
						"value":shot["data"][personID]["value"],
						"roomID":shot["data"][personID]["roomID"]
					}
				except:
					print "??"
					print shot[personID]
			result+=[shot]
		
		return self._encode(result,True)

	def QueryEvents(self,person,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			},
			"personID":person
		}
		projection = {"_id":0}
		iterator = self.events_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for item in iterator:
			result+=[item]
		
		return self._encode(result,True)

	def QueryAllEvents(self,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"_id":0}
		iterator = self.events_col.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for item in iterator:
			result+=[item]
		
		return self._encode(result,True)

	def SaveLocationData(self, person, location):
		self.dbc.db1.coll1.insert({
			"l1":location,
			"person":person,
			"timestamp":datetime.datetime.utcnow()
		})

	def QueryLocationData(self, person):
	#	result = []
#		condition = {
#			"person":person
#		}
#		iterator = self.dbc.db1.coll1.find(condition).sort([("timestamp",pymongo.DESCENDING)])
#		x = list(iterator)
#		y = x[0]
		return "Testing Database"#y['l1']

if __name__ == "__main__":
	dbm=DBMgr()
	dbm._TEST()

