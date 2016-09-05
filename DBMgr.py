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

from Email import SendEmail

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
		self.WATCHDOG_TIMEOUT_USER=self._GetConfigValue("WATCHDOG_TIMEOUT_USER")
		self.WATCHDOG_TIMEOUT_APPLIANCE=self._GetConfigValue("WATCHDOG_TIMEOUT_APPLIANCE")
		

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

####################################################################
## Room ID and Appliance IDs functions #############################
####################################################################
	def RoomIdToName(self,id):
		return self.list_of_rooms[id]["name"]
	def ApplIdToName(self,id):
		return self.list_of_appliances[id]["name"]
	def ApplIdToVal(self,id):
		return self.list_of_appliances[id]["value"]
####################################################################

	def _encode(self,data,isPretty):
		return MongoJsonEncoder().encode(data)
	def __init__(self, start_bg_thread=True):
		self.dbc=pymongo.MongoClient()

		db1 = self.dbc.test_database
		coll1 = db1.test_collection

		self.registration_col1=self.dbc.db.registration_col1
		self.registration_col1.ensure_index('screenName', unique=True)
		self.ranking = self.dbc.db.ranking
		self.ranking.ensure_index('user', unique=True)

		self.suggestionsML = self.dbc.db.suggestionsML
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

		self.watchdogInit()

		if start_bg_thread:
			self.startDaemon()

		## Start the snapshot thread if not running "python DBMgr.py"
		## (perform self-test if it is.)

		##if __name__ != "__main__":
		##	self.recover_from_latest_shot()

	def startDaemon(self):
		t=Thread(target=self._backgroundLoop,args=())
		t.setDaemon(True)
		t.start()

	def recordEvent(self, personID, etype, data):
		self.events_col.insert({
			"personID":personID,
			"type":etype,
			"data":data,
			"timestamp":datetime.datetime.utcnow()
			})

####################################################################
## Login Information, for self.registration_col1 ###################
####################################################################
	def screenNameCheckAvailability(self, screenName):
		return len(list(self.registration_col1.find({"screenName":screenName}))) == 0
	
	def screenNameUpdate(self, screenName, userID):
		return self.registration_col1.update({"userID": userID},
			{"$set": {"screenName": screenName}},
			multi=True)


	def screenNameRegister(self, screenName, userID):
		self.LogRawData({
			"type":"screenNameRegister",
			"time":self._now(),
			"screenName":screenName,
			"userID":userID
			})
		try:
			self.registration_col1.insert({
				"screenName":screenName,
				"userID":userID
				})
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def screenNameLookup(self, screenName):
		ret=list(self.registration_col1.find({"screenName":screenName}))
		if len(ret)!=1:
			return None
		return ret[0]["userID"]
	
	def userIDLookup(self, userID):
		self.LogRawData({
			"type":"userIDLookup",
			"time":self._now(),
			"userID":userID
			})
		ret=list(self.registration_col1.find({"userID":userID}))
		if len(ret)!=1:
			return None
		return ret[0]["screenName"]

####################################################################


	def watchdogInit(self):
		self.watchdogLastSeen_User={}
		self.watchdogLastSeen_Appliance={}

	def watchdogRefresh_User(self, userID):
		if userID not in self.watchdogLastSeen_User:
			self.watchdogLastSeen_User[userID]=0
		self.watchdogLastSeen_User[userID]=max(self._now(), self.watchdogLastSeen_User[userID])

	def watchdogRefresh_Appliance(self, applID):
		if applID not in self.watchdogLastSeen_Appliance:
			self.watchdogLastSeen_Appliance[applID]=0
		self.watchdogLastSeen_Appliance[applID]=max(self._now(), self.watchdogLastSeen_Appliance[applID])


	def watchdogCheck_User(self):
		outOfRange_List=[]
		minTime=self._now()-self.WATCHDOG_TIMEOUT_USER

		for userID in self.watchdogLastSeen_User:
			if self.watchdogLastSeen_User[userID]<minTime:
				outOfRange_List+=[userID]

		self.LogRawData({
			"type":"watchdogCheck_User",
			"time":self._now(),
			"minTime":minTime,
			"outOfRange_List":outOfRange_List,
			"raw":self.watchdogLastSeen_User,
			})

		for userID in outOfRange_List:
			last_seen=self.watchdogLastSeen_User[userID]
			self.ReportLocationAssociation(userID, None, {"Note":"Reported by Watchdog","last_seen": last_seen})


	def watchdogCheck_Appliance(self):
		notWorking_List=[]
		minTime=self._now()-self.WATCHDOG_TIMEOUT_APPLIANCE
		futureTime=self._now()+86400
		
		#for applID in self.watchdogLastSeen_Appliance:
		for applID in self.list_of_appliances:
			if self.list_of_appliances[applID]["value"]>0:
				# for all working(value>0) appliances
				if applID in self.watchdogLastSeen_Appliance:
					if self.watchdogLastSeen_Appliance[applID]<minTime:
						notWorking_List+=[applID]
				else:
					#start-up issue, maybe the first report haven't arrived yet.
					self.watchdogLastSeen_Appliance[applID]=self._now()

		for applID in notWorking_List:
			last_seen=self.watchdogLastSeen_Appliance[applID]
			self.watchdogLastSeen_Appliance[applID]=futureTime
			self.ReportEnergyValue(applID, 0, {"Note":"Reported by Watchdog","last_seen": last_seen})

		title="Energy Monitoring Appliance Down: "+str(notWorking_List)
		body="Dear SysAdmin,\nThe following appliance ID has not been reporting to the system for >15 minutes."
		body+="\n\n"+"\n".join([str(x) for x in notWorking_List])+"\n\n"
		body+="Please debug as appropriate.\nNote: this warning will repeat every 24 hours."
		body+="\n\nSincerely, system watchdog."

		if len(notWorking_List)>0:
			email_ret=SendEmail(title, body)

		self.LogRawData({
			"type":"watchdogCheck_Appliance",
			"time":self._now(),
			"minTime":minTime,
			"notWorking_List":notWorking_List,
			"raw":self.watchdogLastSeen_Appliance,
			})



	def updateUserLocation(self, user_id, in_id=None, out_id=None):
		self.location_of_users[user_id]=in_id
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
		self.watchdogRefresh_Appliance(applianceID)
		
	def getUserLocation(self, user_id):
		return self.location_of_users[user_id]

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
		self.watchdogRefresh_User(personID)

		if roomID!=None and roomID not in self.list_of_rooms:
			"if no legitimate roomID, then he's out of tracking."
			newS=None
			self.recordEvent(personID,"illegitimateLocationReported",roomID)
		else:
			self.recordEvent(personID,"locationChange",roomID)

		self.updateUserLocation(personID, newS, oldS)

		if newS!=None:
			self.list_of_rooms[newS]["phantom_user"]=personID

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

	def CurrentApplianceUsage(self, limit=3):
		ret = {}
		for person in self.location_of_users:
			location = self.location_of_users[person]
			if location not in self.list_of_rooms:
				continue
			appliances = self.list_of_rooms[location]["appliances"]
			applianceValues = []
			applianceIDs = []
			for applianceID in appliances:
				applianceValues.append(self.list_of_appliances[applianceID]["value"])
				applianceIDs.append(applianceID)
			appliances_sorted = sorted(range(len(applianceValues)), key=lambda k:applianceValues[k])
			len_appliances = len(appliances_sorted)
			min_appliances = min(len_appliances, limit)
			rec_appliances = []
			for i in range(min_appliances):
				AID = applianceIDs[appliances_sorted[i]]
				rec_appliances.append(self.list_of_appliances[AID])
			ret[person] = rec_appliances
		return ret
		#appliancesSorted
		#for appliance in self.list_of_appliances:
	#		ret[appliance]=self.list_of_appliances[appliance]["users"]


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
	def _toUnix(self, ts):
		return calendar.timegm(ts.utctimetuple())
	def _backgroundLoop(self):
		print("DBMGR _backgroundLoop started...")
		while True:
			time.sleep(self.SAMPLING_TIMEOUT_LONGEST)
			self.SaveShot()
			self.watchdogCheck_User()
			self.watchdogCheck_Appliance()

	def ShowRealtime(self, person=None, concise=True):
		#save into database, with: timestamp, additional data
		ret={
			"timestamp":self._now()
		}
		if person and person in self.location_of_users:
			roomID=self.location_of_users[person]
			if roomID!=None:
				ret["personal"]=self.calculateRoomFootprint(roomID)
				#ret["location"]=roomID
				ret["location"]=self.list_of_rooms[roomID]
		else:
			ret["rooms"]=self._getShotRooms(concise)
			ret["appliances"]=self._getShotAppliances(concise)
			ret["locations"]=self.location_of_users
			ret["watchdog_user"]=self.watchdogLastSeen_User
			ret["watchdog_appl"]=self.watchdogLastSeen_Appliance
		return self._encode(ret,True)

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

	def BinUsersLocHistory(self, start=-1, end=0):
		# Provide two timestamps as time range; by default, we check "yesterday" (24hr, local timezone)
		# Note: expensive function, called once a day.
		# return format: dict[user_id][timestamp]={"location":?,"value":?}
		if start==-1:
			end=time.mktime(datetime.date.today().timetuple())
			start=end-86400
		
		dict_raw_snapshots={}
		dict_users={}

		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"_id":0}
		iterator = self.snapshots_col_users.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for snapshot in iterator:
			ts=self._toUnix(snapshot["timestamp"])
			dict_raw_snapshots[ts]=snapshot
			for user_id in snapshot["data"]:
				if user_id not in dict_users:
					dict_users[user_id]=[]
		
		for ts in dict_raw_snapshots:
			for user_id in dict_users:
				if user_id not in dict_raw_snapshots[ts]["data"]:
					dict_users[user_id]+=[{
						"timestamp":ts,
						"location":None,
					}]
				else:
					item=dict_raw_snapshots[ts]["data"][user_id]
					item["timestamp"]=ts
					dict_users[user_id]+=[item]
		
		step=15*60
		bins_headers=range(int(start),int(end),int(step))
		bins_ranges=[range(x,x+step) for x in bins_headers]
		def get_majority(lst):
			return max(set(lst), key=lst.count)
		def get_average(lst):
			return sum(lst)/(1.0*len(lst))

		for user_id in dict_users:
			time_series=dict_users[user_id]
			return_bins={}
			for bin_range in bins_ranges:
				in_range=[x for x in time_series if x["timestamp"] in bin_range]
				majority_loc=get_majority([x["location"] for x in in_range])
				if majority_loc==None:
					return_bins[bin_range.start]={"location":None, "value":0}
				else:
					majority_average=get_average([x["value"] for x in in_range if x["location"]==majority_loc])
					return_bins[bin_range.start]={"location":majority_loc,"value":majority_average}
			dict_users[user_id]=return_bins

		return dict_users

	def BinApplPowerHistory(self, start=-1, end=0):
		# Similar to user history yesterday.
		# return format: dict[appl_id][timestamp]={"user_list":[],"value":?}
		if start==-1:
			end=time.mktime(datetime.date.today().timetuple())
			start=end-86400
		
		dict_raw_snapshots={}
		dict_appls={}

		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"_id":0}
		iterator = self.snapshots_col_appliances.find(condition, projection).sort([("timestamp", pymongo.DESCENDING)])
		for snapshot in iterator:
			ts=self._toUnix(snapshot["timestamp"])
			dict_raw_snapshots[ts]=snapshot
			for appl_id in snapshot["data"]:
				if appl_id not in dict_appls:
					dict_appls[appl_id]=[]

		for ts in dict_raw_snapshots:
			for appl_id in dict_appls:
				if appl_id not in dict_raw_snapshots[ts]["data"]:
					dict_appls[appl_id]+=[{
						"timestamp":ts,
						"location":None,
					}]
				else:
					item=dict_raw_snapshots[ts]["data"][appl_id]
					item["timestamp"]=ts
					dict_appls[appl_id]+=[item]
		
		step=15*60
		bins_headers=range(int(start),int(end),int(step))
		bins_ranges=[range(x,x+step) for x in bins_headers]
		def get_average(lst):
			return sum(lst)/(1.0*len(lst))
		for appl_id in dict_appls:
			time_series=dict_appls[appl_id]
			return_bins={}
			for bin_range in bins_ranges:
				in_range=[x for x in time_series if x["timestamp"] in bin_range]
				avg_power=get_average([x["value"] for x in in_range])
				avg_users=get_average([x["total_users"] for x in in_range])
				return_bins[bin_range.start]={"avg_users":avg_users, "value":avg_power}	
			dict_appls[appl_id]=return_bins

		return dict_appls
	
		
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

		self.registration_col1=self.dbc.test.registration_col1
		self.registration_col1.ensure_index('screenName', unique=True)
		

		# case 1: add a consumption value, put two users, the users get shared energy consumption
		self.ReportEnergyValue("nwc1000m_a2_plug2", 2, {"testing":True,"message":"unit test"})
		
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

		# check phantom user
		if self.list_of_rooms["nwc1000m_a1"]["phantom_user"] != "testUser1":
			print("phantom_user not set correctly.")
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

		NewSN="NEW_Name"
		print(self.screenNameUpdate(NewSN, ID))
		if self.userIDLookup(ID) != NewSN:
			print("userIDLookup() unexpected after screenNameUpdate()")
			print(list(self.registration_col1.find()))
			sys.exit(-1)



		print("Self-test succeeded, exit now.")
		sys.exit(0)
		## IOS RELATED, DON'T TOUCH




####################################################################
## Ranking Functions, for self.ranking #############################
####################################################################

	def registerForRanking(self, user):
		self.ranking.insert({
			"user":user,
			"balance":0
			})

	def rankingUpdateName(self, oldName, newName):
		itm = self.ranking.find_one({"user": oldName})
		object_id = itm.get('_id')
		return self.ranking.update({'_id': object_id},
			{"$set": {"user": newName}},
			multi=True)

	def registerForRankingInfo(self, user, lab, gender, affiliation):
		self.ranking.insert({
			"user":user,
			"balance":0,
			"lab":lab,
			"gender":gender,
			"affiliation":affiliation
			})

	def updateRankingData(self, user, balance):
		self.ranking.update({
			"user": user
			},
			{
			"user": user,
			"balance": balance
			},
			True
			)

	def updateUserBalance(self, user, balance):
		old_balance = self.getUserBalance(user)
		self.updateRankingData(user, old_balance + balance)

	def getRankingData(self):
		return self.ranking.find().sort([("balance",-1),("user",1)])

	def getUserBalance(self, user):
		U = self.ranking.find_one({"user":user})
		if (U == None):
			return False
		return U["balance"]




####################################################################
## Machine Learning Functions, for self.suggestionsML ##############
####################################################################

	def submitAcceptedSuggestion(self, sugType, startRoom, endRoom, ToD, applianceNum):
		self.suggestionsML.insert({
			"type":sugType,
			"startRoom":startRoom,
			"endRoom":endRoom,
			"time":ToD,
			"applianceNum": applianceNum
			})

####################################################################

	def SaveLocationData(self, person, location):
		self.dbc.db1.coll1.insert({
			"location":location,
			"person":person,
			"timestamp":datetime.datetime.utcnow()
		})

	def DestroyLocationData(self):
		self.dbc.db1.coll1.remove({})

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
	dbm=DBMgr(False)
	dbm._TEST()
	## Beware, the _TEST will terminate the script.
