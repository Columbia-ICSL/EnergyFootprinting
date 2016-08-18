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
	print("Got log:"+msg)
	print(obj)
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

	def _ReadConfigs(self):
		self.ROOM_DEFINITION=self._GetConfigValue("ROOM_DEFINITION")
		self.APPLIANCE_DEFINITION=self._GetConfigValue("APPLIANCE_DEFINITION")
		self.SAMPLING_TIMEOUT_SHORTEST=self._GetConfigValue("SAMPLING_TIMEOUT_SHORTEST")
		self.SAMPLING_TIMEOUT_LONGEST=self._GetConfigValue("SAMPLING_TIMEOUT_LONGEST")

	def _ConstructInMemoryGraph(self):
		self.list_of_rooms={};
		self.list_of_appliances={};
		self.location_of_users={};

		for room in self.ROOM_DEFINITION:
			room["appliances"]=[]
			room["users"]=[]
			self.list_of_rooms[room["id"]]=room

		for appliance in self.APPLIANCE_DEFINITION:
			appliance["value"]=0
			appliance["total_users"]=0
			appliance["rooms"].sort()
			self.list_of_appliances[appliance["id"]]=appliance
			for roomID in appliance["rooms"]:
				self.list_of_rooms[roomID]["appliances"]+=[appliance["id"]]

		for room in self.ROOM_DEFINITION:
			self.list_of_rooms[room["id"]]["appliances"].sort()
		## Finished appliance bipartite graph.


	def _encode(self,data,isPretty):
		return MongoJsonEncoder().encode(data)
	def __init__(self):
		self.dbc=pymongo.MongoClient()

		db1 = self.dbc.test_database
		coll1 = db1.test_collection

		self.registration_col=self.dbc.db.registration_col
		self.registration_col.ensure_index('screen_name', unique=True)
		#user registration
		self.config_col=self.dbc.db.config
		#metadata col
		self.raw_data=self.dbc.db.raw_data
		#any raw data document.
		self.events_col=self.dbc.db.events_col
		#any events

		self.snapshots_col_rooms=self.dbc.db.snapshots_col_rooms
		self.snapshots_col_appliances=self.dbc.db.snapshots_col_appliances
		self.snapshots_col_users=self.dbc.db.snapshots_col_users
		#snapshot storage

		self._latestSuccessShot=0

		self._ReadConfigs()
		## Data Structure Init: bipartite graph between rooms and appls
		## TODO: Add a web interface to update config in db, and pull new config into memory.

		self._ConstructInMemoryGraph()
		## Construct bipartite graph. no recovery for now

		if __name__ != "__main__":
			self.startDaemon()
		## Start the snapshot thread if not running "python DBMgr.py"
		## (perform self-test if it is.)

		##if __name__ != "__main__":
		##	self.recover_from_latest_shot()

	def startDaemon(self):
		t=Thread(target=self._loopSaveShot,args=())
		t.setDaemon(True)
		t.start()

	def recordEvent(self, personID, etype, data):
		self.events_col.insert({
			"personID":personID,
			"type":etype,
			"data":data,
			"timestamp":datetime.datetime.utcnow()
			})

	def screenNameCheckAvailability(self, screenName):
		return len(list(self.registration_col.find({"screenName":screenName}))) == 0
		
	def screenNameRegister(self, screenName, userID):
		try:
			self.registration_col.insert({
				"screenName":screenName,
				"userID":userID,
				})
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def screenNameLookup(self, screenName):
		ret=list(self.registration_col.find({"screenName":screenName}))
		if len(ret)!=1:
			return None
		return ret[0]["userID"]
	
	def userIDLookup(self, userID):
		ret=list(self.registration_col.find({"userID":userID}))
		if len(ret)!=1:
			return None
		return ret[0]["screenName"]

	def updateUserLocation(self, user_id, in_id=None, out_id=None):
		self.location_of_users[user_id]=in_id
		for room in self.list_of_rooms:
			print(room),print(len(self.list_of_rooms[room]["users"]))
		if in_id==out_id:
			return
		## TODO: optimize, merge In-ops and Out-ops and remove unnecessary update to common appliances
		if in_id!=None and self.list_of_rooms[in_id]!=None:
			self.list_of_rooms[in_id]["users"]+=[user_id]
			for applianceID in self.list_of_rooms[in_id]["appliances"]:
				self.list_of_appliances[applianceID]["total_users"]+=1
		if out_id!=None and self.list_of_rooms[out_id]!=None:
			self.list_of_rooms[out_id]["users"].remove(user_id)
			for applianceID in self.list_of_rooms[out_id]["appliances"]:
				self.list_of_appliances[applianceID]["total_users"]-=1
		
	def updateApplianceValue(self, applianceID, value):
		self.list_of_appliances[applianceID]["value"]=value

	def calculateRoomFootprint(self, roomID):
		app_list=self.list_of_rooms[roomID]["appliances"]
		ret={
			"value":0,
			"consumptions":[]
		}
		total_con=0.0
		for applianceID in app_list:
			app=self.list_of_appliances[applianceID]
			app["share"]=app["value"]/(1.0*app["total_users"])

			total_con+=app["share"]
			ret["consumptions"]+=[app]
		ret["value"]=total_con
		return ret

	def LogRawData(self,obj):
		obj["_log_timestamp"]=datetime.datetime.utcnow()
		self.raw_data.insert(obj)



	def ReportEnergyValue(self, applianceID, value, raw_data=None):
		"maintenance tree node's energy consumption item, and update a sum value"
		known_room=None
		try:
			app=self.list_of_appliances[applianceID]
			known_room=app["rooms"]
			self.updateApplianceValue(app["id"], value)

		except:
			add_log("failed to report energy value on device",{
				"known_room":known_room,
				"deviceID":applianceID,
				"value":value,
				"raw":raw_data
				})
			return

		self.LogRawData({
			"type":"energy_report",
			"roomID":known_room,
			"applianceID":applianceID,
			"value":value,
			"raw":raw_data
			})
		

	def ReportLocationAssociation(self, personID, roomID, raw_data=None):
		oldS=None
		newS=roomID
		if personID in self.location_of_users:
			oldS=self.location_of_users[personID]

		self.LogRawData({
			"type":"location_report",
			"roomID":roomID,
			"personID":personID,
			"raw":raw_data,
			"oldS":oldS,
			"newS":newS
			})

		if roomID not in self.list_of_rooms:
			"if no legitimate roomID, then he's out of tracking."
			newS=None
			self.recordEvent(personID,"illegitimateLocationReported",roomID)
		else:
			self.recordEvent(personID,"locationChange",roomID)

		self.updateUserLocation(personID, newS, oldS)

		"people change; should we update now?"
		self.OptionalSaveShot();

	def OptionalSaveShot(self):
		"minimum interval: 10s; in lieu with regular snapshotting"
		if self._latestSuccessShot< self._now() -10 :
			self.SaveShot();

	# TODO: think about what to drop in concise mode
	def _getShotRooms(self, concise=True):
		return self.list_of_rooms

	def CurrentOccupancy(self):
		ret={}
		for roomID in self.list_of_rooms:
			ret[roomID]=self.list_of_rooms[roomID]["users"]
		return ret

	def _getShotAppliances(self, concise=True):
		return self.list_of_appliances

	def _getShotPersonal(self):
		personal_consumption={}
		cached_per_room_consumption={}
		for user_id in self.location_of_users:
			try:
				roomID=self.location_of_users[user_id]
				if roomID==None:
					continue
				if (roomID not in cached_per_room_consumption):
					cached_per_room_consumption[roomID]=self.calculateRoomFootprint(roomID)
				personal_consumption[user_id]=cached_per_room_consumption[roomID]
				personal_consumption[user_id]["location"]=roomID
			except:
				add_log("fail to trace person's consumption; id:",user_id)

		return personal_consumption

	def SaveShot(self, any_additional_data=None):
		#save into database, with: timestamp, additional data
		self.snapshots_col_rooms.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":self._getShotRooms()
			})

		self.snapshots_col_appliances.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":self._getShotAppliances()
			})
			
		self.snapshots_col_users.insert({
			"timestamp":datetime.datetime.utcnow(),
			"data":self._getShotPersonal()
			})

		self._latestSuccessShot=self._now();
		return True
		"2. TODO: maintain last entrance list of all rooms; check all occupants.number==0 rooms, make the last person liable."
		"3. possible accumulation at different tier?? like every 600 seconds?"
		

	def _now(self):
		return calendar.timegm(datetime.datetime.utcnow().utctimetuple())
	def _loopSaveShot(self):
		while True:
			time.sleep(self.SAMPLING_TIMEOUT_LONGEST)
			self.SaveShot()

	def ShowRealtime(self, person=None, concise=True):
		#save into database, with: timestamp, additional data
		ret={
			"timestamp":self._now()
		}
		if person and person in self.location_of_users:
			roomID=self.location_of_users[person]
			if roomID!=None:
				ret["personal"]=self.calculateRoomFootprint(roomID)
		else:
			ret["rooms"]=self._getShotRooms(concise)
			ret["appliances"]=self._getShotAppliances(concise)
			ret["locations"]=self.location_of_users
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
		iterator = self.snapshots_col_rooms.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
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
		iterator = self.snapshots_col_users.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			if person in shot["data"]:
				item=shot["data"][person]
				item["timestamp"]=shot["timestamp"]
				result+=[item]
		
		return self._encode(result,True)


	def QueryPersonAll(self,start,end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"_id":0}

		iterator = self.snapshots_col_users.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			item=shot["data"]
			item["timestamp"]=shot["timestamp"]
			result+=[item]
		
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
		
	def _TEST(self):
		# unit testing, after init.

		#cleanup
		self.dbc.drop_database('test')

		# Redirect storage
		self.snapshots_col_rooms=self.dbc.test.snapshots_col_rooms
		self.snapshots_col_appliances=self.dbc.test.snapshots_col_appliances
		self.snapshots_col_users=self.dbc.test.snapshots_col_users
		
		self.raw_data=self.dbc.test.raw_data
		self.events_col=self.dbc.test.events_col

		self.registration_col=self.dbc.test.registration_col
		self.registration_col.ensure_index('screen_name', unique=True)
		

		# case 1: add a consumption value, put two users, the users get shared energy consumption
		self.ReportEnergyValue("nwc1000m_a2_plug", 2, {"testing":True,"message":"unit test"})
		
		self.ReportLocationAssociation("testUser2", "nwc1003b",  {"testing":True,"message":"unit test"})
		self.ReportLocationAssociation("testUser1", "nwc1000m_a1",  {"testing":True,"message":"unit test"})
		self.ReportLocationAssociation("testUser2", "nwc1000m_a2",  {"testing":True,"message":"unit test"})

		self.ReportEnergyValue("nwc1000m_light", 100, {"testing":True,"message":"unit test"})
		self.ReportEnergyValue("nwc1008_light", 10, {"testing":True,"message":"unit test"})

		result=self._getShotPersonal()

		if result["testUser1"]["value"]!=50 or result["testUser2"]["value"]!=52 :
			print("Unexpected personal snapshot: expecting energy split.", result)
			sys.exit(-1)

		# case 2: move the user away, the other user gets all consumption
		self.ReportLocationAssociation("testUser1", "nwc1008",  {"testing":True,"message":"unit test"})
		result=self._getShotPersonal()
		if result["testUser1"]["value"]!=10 or result["testUser2"]["value"]!=102 :
			print("Unexpected personal snapshot: expecting full responsibility.", result)
			sys.exit(-1)


		# test CurrentOccupancy()
		result=self.CurrentOccupancy()
		if result["nwc1008"] != ["testUser1"] or result["nwc1000m_a2"] != ["testUser2"] :
			print("CurrentOccupancy() didn't return expected list.", result)
			sys.exit(-1)

		# case 3: TODO: take a snapshot manually, and check if it's intended
		self.SaveShot()
		if False:
			sys.exit(-1)
		# case 4: TODO: optional save should not be triggered immediately
		# self.OptionalSaveShot()
		# should be triggered after minimum sampling interval
		# sleep()
		# self.OptionalSaveShot()


		# Test User signup:
		ID="000001"
		SN="my_screen_name_lol"
		# ID is available
		if self.screenNameCheckAvailability(SN) != True:
			print("screenNameCheckAvailability() not passed?")
			sys.exit(-1)
		# add user, should success
		if self.screenNameRegister(SN, ID) != True:
			print("screenNameRegister() failed?")
			sys.exit(-1)

		# add another time, should fail
		if self.screenNameRegister(SN, ID) != False:
			print("screenNameRegister() succeeded when registering again?")
			sys.exit(-1)
		# ID is not available
		if self.screenNameCheckAvailability(SN) != False:
			print("screenNameCheckAvailability() passed for existing ID?")
			sys.exit(-1)
		# lookup users, id should match
		if self.userIDLookup(ID) != SN:
			print("userIDLookup() unexpected")
			sys.exit(-1)
		if self.screenNameLookup(SN) != ID:
			print("screenNameLookup() unexpected")
			sys.exit(-1)


		print("Self-test succeeded, exit now.")
		sys.exit(0)
		## IOS RELATED, DON'T TOUCH


	def SaveLocationData(self, person, location):
		self.dbc.db1.coll1.insert({
			"l1":location,
			"person":person,
			"timestamp":datetime.datetime.utcnow()
		})

	def QueryLocationData(self, person):
		result = []
		condition = {
			"person":person
		}
		iterator = self.dbc.db1.coll1.find(condition).sort([("timestamp",pymongo.DESCENDING)])
		x = list(iterator)
		y = x[0]
		return y['l1']

if __name__ == "__main__":
	dbm=DBMgr()
	dbm._TEST()
	## Beware, the _TEST will terminate the script.
