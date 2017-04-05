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
#from past.builtins import xrange

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

def get_majority(lst):
	return max(set(lst), key=lst.count)
def get_average(lst):
	return sum(lst)/(1.0*len(lst))

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

	def _GracefulReloadGraph(self):
		print('Reloading values...')
		try:
			latest_snapshot=self.snapshots_col_appliances.find_one(sort=[("timestamp", pymongo.DESCENDING)]);
			if latest_snapshot!=None:
				for applianceID in latest_snapshot["data"]:
					value=latest_snapshot["data"][applianceID]["value"]
					if value>0:
						print('Recovered Appliance:',applianceID, value)
						self.updateApplianceValue(applianceID, value)
			else:
				print('Appliance latest snapshot not found.')
		except Exception:
			add_log('failed to recover appliance power values during graceful reload.',latest_snapshot)

		try:
			latest_snapshot=self.snapshots_col_users.find_one(sort=[("timestamp", pymongo.DESCENDING)]);
			if latest_snapshot!=None:
				for userID in latest_snapshot["data"]:
					roomID=latest_snapshot["data"][userID]["location"]
					print('Recovered Location:',userID,roomID)
					#self.updateUserLocation(userID, roomID, None)
			else:
				print('User location latest snapshot not found.')
		except Exception:
			add_log('failed to recover user locations during graceful reload.',latest_snapshot)
	

####################################################################
## Room ID and Appliance IDs functions #############################
####################################################################
	def RoomIdToName(self,id):
		return self.list_of_rooms[id]["name"]
	def RoomIDToLab(self,id):
		return self.list_of_rooms[id]["lab"]
	def ApplIdToName(self,id):
		return self.list_of_appliances[id]["name"]
	def ApplIdToVal(self,id):
		return self.list_of_appliances[id]["value"]
	def ApplIdToType(self,id):
		return self.list_of_appliances[id]["type"]
	def ApplIdToRoom(self,id):
		return self.list_of_appliances[id]["room"]
####################################################################

	def _encode(self,data,isPretty):
		return MongoJsonEncoder().encode(data)
	def __init__(self, start_bg_thread=True):
		self.dbc=pymongo.MongoClient()

		db1 = self.dbc.test_database
		coll1 = db1.test_collection

		self.registration_col1=self.dbc.db.registration_col1
		self.ranking = self.dbc.db.ranking
		self.indirectSensing = self.dbc.db.indirectSensing
		self.particleSensor = self.dbc.db.particleSensor
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

		self.pushManagement_push_col=self.dbc.db.pushManagement_push_col
		self.pushManagement_disp_col=self.dbc.db.pushManagement_disp_col
		#push management timestamp storage

		self._latestSuccessShot=0

		self._ReadConfigs()
		## Data Structure Init: bipartite graph between rooms and appls
		## TODO: Add a web interface to update config in db, and pull new config into memory.

		self._ConstructInMemoryGraph()
		## Construct bipartite graph.
		self._GracefulReloadGraph()
		## Read appliance values from database; TODO: occupants location

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
## Data Visualization ##############################################
####################################################################

	def buildingFootprint(self, start, end):
		### HERE ###
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		iterator = self.snapshots_col_appliances.find(condition).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			lst = shot["data"]
			energyVal = 0
			item = {}
			item["timestamp"] = shot["timestamp"]
			for app in lst:
				energyVal += lst[app]["value"]
			item["data"] = energyVal
			result += [item]
		return self._encode(result, True)

	def buildingFootprintDisaggregated(self, start, end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		iterator = self.snapshots_col_appliances.find(condition).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			lst = shot["data"]
			energyVal = {}
			energyVal["HVAC"] = 0
			energyVal["Light"] = 0
			energyVal["Electrical"] = 0
			item = {}
			item["timestamp"] = shot["timestamp"]
			for app in lst:
				applType = ApplIdToType(app)
				if (applType not in energyVal):
					continue
				energyVal[applType] += lst[app]["value"]
			item["data"] = energyVal
			result += [item]
		return self._encode(result, True)

	def personalFootprint(self, person, start, end):
		result=[]
		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		iterator = self.snapshots_col_users.find(condition).sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			if person in shot["data"]:
				item=shot["data"][person]
				item["timestamp"]=shot["timestamp"]
				result+=[item]
		
		return self._encode(result,True)		













####################################################################
## Login Information, for self.registration_col1 ###################
####################################################################
	def screenNameCheckAvailability(self, screenName):
		return len(list(self.registration_col1.find({"screenName":screenName}))) == 0
	
	def deviceIDCheckAvailability(self, deviceID):
		return len(list(self.registration_col1.find({"userID":deviceID}))) == 0
		
	def screenNameUpdate(self, screenName, userID):
		try:
			self.registration_col1.update({"userID": userID},
				{"$set": {"screenName": screenName}},
				multi=True)
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def fullRegistration(self, deviceID, name, email, password):
		try:
			self.registration_col1.insert({
				"userID": deviceID})
			print("successfully inserted new user")
			self.registration_col1.update({"userID": deviceID},{"$set":{
				"name": name,
				"email": email,
				"password": password,
				"control": True,
				"balance": 0,
				"tempBalance": 0,
				"loggedIn": True
				}})
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def checkLoginFlow(self, deviceID):
		user = self.registration_col1.find_one({"userID": deviceID})
		if user is not None:
			if user.get("loggedIn"):
				return "0" #user is logged in
			else:
				return "1" #user not logged in
		return "404" #user not registered

	def getNameFromDeviceID(self, deviceID):
		user = self.registration_col1.find_one({"userID": deviceID})
		return user.get("name")
		
	def logout(self, deviceID):
		try:
			self.registration_col1.update({"userID": deviceID},
				{"$set":{"loggedIn": False}})
			return "0"
		except pymongo.errors.DuplicateKeyError:
			return "1"

	def login(self, deviceID, email, password):
		user = self.registration_col1.find_one({"userID": deviceID})
		if user is not None:
			if (user.get("email") == email) and (user.get("password") == password):
				self.registration_col1.update({"userID":deviceID}, {"$set":{"loggedIn":True}})
				return "0"

			else:
				return "1"
		return "404"

	def changeEmailAndPassword(self, deviceID, email, password):
		try:
			self.registration_col1.update({"userID":deviceID}, {"$set":{"email":email}})
			self.registration_col1.update({"userID":deviceID}, {"$set":{"password":password}})
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def addPushToken(self, deviceID, token):
		try:
			self.registration_col1.update({"userID":deviceID}, {"$set":{"token":token}})
			return "0"
		except pymongo.errors.DuplicateKeyError:
			return "404"
		return "400"





	def screenNameRegister(self, screenName, userID, control=True):
		self.LogRawData({
			"type":"screenNameRegister",
			"time":self._now(),
			"screenName":screenName,
			"userID":userID,
			"rewards":0,
			"tempRewards":0
			})
		try:
			self.registration_col1.insert({
				"screenName":screenName,
				"userID":userID,
				"control":control,
				"balance":0,
				"tempBalance":0
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
		ret=list(self.registration_col1.find({"userID":userID}))
		if len(ret)!=1:
			return None
		if "name" in ret[0]:
			return ret[0]["name"]
		return ret[0]["screenName"]
	
	def getControl(self, userID):
		user = self.registration_col1.find_one({"userID":userID})
		if user != None:
			if "control" in user:
				return user.get("control")
		return True

	def userIDRemoveAll(self, userID):
		self.registration_col1.remove({"userID":userID})

####################################################################
##  Message last-pushed/last-seen information  #####################
####################################################################
	def pushManagementPushUpdate(self, key, now=None):
		if now==None:
			now=self._now()
		self.pushManagement_push_col.update(
			{"_id":key},
			{"$set":{"timestamp":now}},
			upsert=True)


	def pushManagementDispUpdate(self, key, now=None):
		if now==None:
			now=self._now()
		self.pushManagement_disp_col.update(
			{"_id":key},
			{"$set":{"timestamp":now}},
			upsert=True)
		
	def pushManagementPushCheck(self, key, notSentSince):
		#return True if the message haven't been sent recently (last sent <= notSentSince)
		latest=0
		item=self.pushManagement_push_col.find_one({"_id":key})
		if item!=None:
			latest=item["timestamp"]
		return latest <= notSentSince
		
	def pushManagementDispCheck(self, key, notSentSince):
		#ditto.
		latest=0
		item=self.pushManagement_disp_col.find_one({"_id":key})
		if item!=None:
			latest=item["timestamp"]
		return latest <= notSentSince
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

	def watchdogUserLastSeen(self, userID):
		if (userID in self.watchdogLastSeen_User):
			return self.watchdogLastSeen_User[userID]
		return None

	def watchdogCheck_User(self):
		outOfRange_List=[]
		minTime=self._now()-self.WATCHDOG_TIMEOUT_USER

		for userID in self.watchdogLastSeen_User:
			if self.watchdogLastSeen_User[userID]<minTime:
				outOfRange_List+=[userID]
				if userID in self.location_of_users:
					oldS=self.location_of_users[userID]
					self.updateUserLocation(userID, "outOfLab", oldS)
		for userID in self.location_of_users:
			if userID not in self.watchdogLastSeen_User:
				oldS=self.location_of_users[userID]
				self.updateUserLocation(userID, "outOfLab", oldS)

		self.LogRawData({
			"type":"watchdogCheck_User",
			"time":self._now(),
			"minTime":minTime,
			"outOfRange_List":outOfRange_List,
			"raw":self.watchdogLastSeen_User,
			})

		for userID in outOfRange_List:
			if (userID in self.watchdogLastSeen_User):
				last_seen=self.watchdogLastSeen_User[userID]
			else:
				last_seen=None
			#self.ReportLocationAssociation(userID, "outOfLab", {"Note":"Reported by Watchdog","last_seen": last_seen})


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
			if (user_id in self.list_of_rooms[out_id]["users"]):
				self.list_of_rooms[out_id]["users"].remove(user_id)
				for applianceID in self.list_of_rooms[out_id]["appliances"]:
					self.list_of_appliances[applianceID]["total_users"]-=1
		
	def updateApplianceValue(self, applianceID, value):
		self.list_of_appliances[applianceID]["value"]=int(value)

	def calculateEnergyFootprint(self, roomID):
		ret={
			"value":0,
			"HVAC":0,
			"Light":0,
			"Electrical":0
		}
		if (roomID is None):
			return ret
		app_list=self.list_of_rooms[roomID]["appliances"]
		total_con = 0.0
		print("starting appliances")
		for applianceID in app_list:
			app = self.list_of_appliances[applianceID]
			appValue = app["value"]/(1.0*app["total_users"])
			total_con += appValue
			if (app["type"] == "Electrical"):
				ret["Electrical"] += appValue
				continue
			if (app["type"] == "HVAC"):
				ret["HVAC"] += appValue
				continue
			if (app["type"] == "Light"):
				ret["Light"] += appValue
		ret["value"]=total_con
		return self._encode(ret, False)

	def buildingEnergyFootprint(self):
		ret={
			"value":0,
			"HVAC":0,
			"Light":0,
			"Electrical":0
		}
		app_list=self.list_of_appliances
		total_con = 0.0
		print("starting appliances")
		for applianceID in app_list:
			app = self.list_of_appliances[applianceID]
			total_con += app["value"]
			if (app["type"] == "Electrical"):
				ret["Electrical"] += appValue
				continue
			if (app["type"] == "HVAC"):
				ret["HVAC"] += appValue
				continue
			if (app["type"] == "Light"):
				ret["Light"] += appValue
		ret["value"]=total_con
		return self._encode(ret, False)





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
			if (applianceID not in self.list_of_appliances):
				print("applianceID " + applianceID + " not in list of appliances.")
				return
			app=self.list_of_appliances[applianceID]
			known_room=app["rooms"]
			if value<0:
				add_log("Negative value found on energy report?",{
					"deviceID":applianceID,
					"value":value,
					"raw":raw_data
					})
				return
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
	
	def getUserLocalizationAPI(self):
		ret = {}
		roomDict = {}
		for room in self.list_of_rooms:
			appliances = self.list_of_rooms[room]["appliances"]
			room_val = 0.0
			for appliance in appliances:
				room_val += self.list_of_appliances[appliance]["value"]
			numUsers = len(self.list_of_rooms[room]["users"])
			if numUsers > 0:
				roomDict[room] = room_val/numUsers
			else:
				roomDict[room] = room_val
		timeNow = self._now()
		#print("\n\n")
		#print("Users in the space:")
		#print(self.location_of_users)
		#print("\n\n")
		for user in self.location_of_users:
			loc = self.location_of_users[user]
			if loc not in roomDict:
				print "no location found"
				continue
			screenName = self.userIDLookup(user)
			timeSinceLastSeen = -1
			if (self.watchdogUserLastSeen(user) is not None):
				timeSinceLastSeen = timeNow-self.watchdogUserLastSeen(user)
			ret[screenName] = (roomDict[loc], loc, timeSinceLastSeen)
		#print("\n\n\n")
		#print("Location of users:")
		#print(self.location_of_users)
		#print("\n")
		#print(self.watchdogUserLastSeen())
		#print("\n\n\n")
		return self._encode(ret, False)


	def getUserLocation(self, user_id):
		if user_id in self.location_of_users:
			return self.location_of_users[user_id]
		else:
			return None

	def ReportLocationAssociation(self, personID, roomID, raw_data=None):
		#self.watchdogUserLastSeen()
		print("Reporting Location for user:")
		print(personID)
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
			#"if no legitimate roomID, then he's out of tracking."
			newS=None
			self.recordEvent(personID,"illegitimateLocationReported",roomID)
		else:
			self.recordEvent(personID,"locationChange",roomID)

		self.updateUserLocation(personID, newS, oldS)

		if newS!=None:
			self.list_of_rooms[newS]["phantom_user"]=personID
			self.list_of_rooms[newS]["phantom_time"] = int(time.mktime(datetime.datetime.now().timetuple()))

		#"people change; should we update now?"
		self.OptionalSaveShot();

	def OptionalSaveShot(self):
		#"minimum interval: 10s; in lieu with regular snapshotting"
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

	def phantomApplianceUsage(self, delayTime, warningPowerLimit):
		ret = {}
		for roomID in self.list_of_rooms:
			appliances = self.list_of_rooms[roomID]["appliances"]
			occupancy = len(self.list_of_rooms[roomID]["users"])
			if (occupancy > 0):
				continue
			maxPower = 0
			maxAppliance = None
			for applianceID in appliances:
				peopleNumber = self.list_of_appliances[applianceID]["total_users"]
				actionable = self.list_of_appliances[applianceID]["actionable"]
				if (peopleNumber != 0 or not actionable):
					continue
				powerVal = self.list_of_appliances[applianceID]["value"]
				if ((powerVal > maxPower) and (powerVal > warningPowerLimit)):
					maxPower = powerVal
					maxAppliance = self.list_of_appliances[applianceID]
			if (maxAppliance == None):
				continue
			if "phantom_user" in self.list_of_rooms[roomID]:
				phantomUser = self.list_of_rooms[roomID]["phantom_user"]
			else:
				continue
			userLoc = self.getUserLocation(phantomUser)
			if userLoc is not None:
				if maxAppliance["id"] in self.list_of_rooms[userLoc]["appliances"]:
					print("Warning Log: user moved to a different space with same appliance footprint")
					continue
			if "phantom_time" in self.list_of_rooms[roomID]:
				phantomTime = self.list_of_rooms[roomID]["phantom_time"]
				curtime = int(time.mktime(datetime.datetime.now().timetuple()))
				if (curtime > phantomTime + delayTime):
					continue
			print("Phantom: {0} Suggestion: {1}".format(phantomUser, roomID))
			if ((phantomUser is not None) and (phantomTime is not None)):
				ret[phantomUser] = (self.RoomIdToName(roomID), maxAppliance, maxPower, self.RoomIDToLab(roomID))
				#TODO: if there is more than 1 room
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

	def _getShotPersonal(self, concise=True):
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
	def ShowRealtimePersonalSummary(self, concise=True):
		ret=self._getShotPersonal()
		total=0
		for userID in ret:
			value=ret[userID]["value"]
			if concise:
				ret[userID]={"value":value}

		for applID in self.list_of_appliances:
			total+=self.list_of_appliances[applID]["value"]

		ret["_total"]=total
		return self._encode(ret,True)

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
			ret["personal"]=self._getShotPersonal(concise)
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

	def QueryPersonPersonalConcise(self,person,start,end):
		binnedData={}
		interval=5*60 # 5 minutes

		condition = {
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}
		projection = {"data."+person:1,"timestamp":1,"_id":0}
		iterator = self.snapshots_col_users.find(condition, projection)#.sort([("timestamp", pymongo.DESCENDING)])
		for shot in iterator:
			binId=self._toUnix(shot["timestamp"])//interval
			if binId not in binnedData:
				binnedData[binId]=[]
			if person in shot["data"]:
				item=shot["data"][person]
				binnedData[binId].append(item)
			else:
				item={"location":None,"value":0}
				binnedData[binId].append(item)

				#item["timestamp"]=shot["timestamp"]
				#result+=[item]

		data={}
		for binId in binnedData:
			binItems=binnedData[binId]
			majority_loc=get_majority([item["location"] for item in binItems])
			average_power=get_average([item["value"] for item in binItems])
			if majority_loc!=None:
				majority_loc=self.RoomIdToName(majority_loc)
			data[binId*interval]=(majority_loc, average_power)

		realtime_consumptions={"value":0, "consumptions":[],"location":None}
		if person in self.location_of_users:
			location=self.location_of_users[person]
			if location!=None:
				realtime_consumptions=self.calculateRoomFootprint(location)
				realtime_consumptions["location"]=self.RoomIdToName(location)
		return self._encode({
			"data":data,
			"realtime":realtime_consumptions
			},True)

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
		iterator = self.snapshots_col_users.find(condition, projection)#.sort([("timestamp", pymongo.DESCENDING)])
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
		bins_headers=xrange(int(start),int(end),int(step))

		for user_id in dict_users:
			time_series=dict_users[user_id]
			return_bins={}
			for bin_start in bins_headers:
				in_range=[x for x in time_series if x["timestamp"] >= bin_start and  x["timestamp"] <= bin_start+step]
				if (len(in_range) == 0):
					majority_loc = None
				else:
					majority_loc=get_majority([x["location"] for x in in_range])
				if majority_loc==None:
					return_bins[bin_start]={"location":None, "value":0}
				else:
					majority_average=get_average([x["value"] for x in in_range if x["location"]==majority_loc])
					return_bins[bin_start]={"location":majority_loc,"value":majority_average}
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
		iterator = self.snapshots_col_appliances.find(condition, projection)#.sort([("timestamp", pymongo.DESCENDING)])
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
						"total_users":0,
						"value":0
					}]
				else:
					item=dict_raw_snapshots[ts]["data"][appl_id]
					item["timestamp"]=ts
					dict_appls[appl_id]+=[item]
		
		step=15*60
		bins_headers=xrange(int(start),int(end),int(step))
		#bins_ranges=[xrange(x,x+step) for x in bins_headers]

		for appl_id in dict_appls:
			time_series=dict_appls[appl_id]
			return_bins={}
			for bin_start in bins_headers:
				in_range = [x for x in time_series if x["timestamp"] >= bin_start and  x["timestamp"] <= bin_start+step]
				if (len(in_range) == 0):
					avg_users = 0
					avg_power = 0
				else:	
					avg_power=get_average([x["value"] for x in in_range])
					avg_users=get_average([x["total_users"] for x in in_range])
				return_bins[bin_start]={"avg_users":avg_users, "value":avg_power}	
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

		self.pushManagement_push_col=self.dbc.test.pushManagement_push_col
		self.pushManagement_disp_col=self.dbc.test.pushManagement_disp_col
		

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

		# check negative energy
		self.ReportEnergyValue("nwc1008_light", 2, {"testing":True,"message":"unit_test_negative_device"})
		self.ReportEnergyValue("nwc1008_light", -3, {"testing":True,"message":"unit_test_negative_device"})
		if self.list_of_appliances["nwc1008_light"]["value"]!=2:
			print('Failed when negative energy report arrives')
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

		# push management test
		now=self._now()

		if self.pushManagementPushCheck("key0", now-1)!=True:
			print("pushManagementPushCheck() key0 unexpected")
			sys.exit(-1)
		self.pushManagementPushUpdate("key0")
		if self.pushManagementPushCheck("key0", now-1)!=False:
			print("pushManagementPushCheck() key0 unexpected")
			sys.exit(-1)
		
		self.pushManagementPushUpdate("key1")
		self.pushManagementPushUpdate("key2",5)
		self.pushManagementDispUpdate("key1")
		self.pushManagementDispUpdate("key2",50)

		if self.pushManagementPushCheck("key1", now-1)!=False:
			print("pushManagementPushCheck() key1 unexpected")
			sys.exit(-1)
		if self.pushManagementPushCheck("key1", now+1)!=True:
			print("pushManagementPushCheck() key1 unexpected")
			sys.exit(-1)

		if self.pushManagementPushCheck("key2", 0)!=False:
			print("pushManagementPushCheck() key2 unexpected")
			sys.exit(-1)
		if self.pushManagementPushCheck("key2", 30)!=True:
			print("pushManagementPushCheck() key2 unexpected")
			sys.exit(-1)
		self.pushManagementPushUpdate("key2",32)
		if self.pushManagementPushCheck("key2", 30)!=False:
			print("pushManagementPushCheck() key2 unexpected")
			sys.exit(-1)
		if self.pushManagementDispCheck("key2", 30)!=False:
			print("pushManagementDispCheck() key2 unexpected")
			sys.exit(-1)
		if self.pushManagementDispCheck("key1", now+10)!=True:
			print("pushManagementDispCheck() key1 unexpected")
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

	def rankingUpdateName(self, oldName, newName, frequency, wifi, public):
		itm = self.ranking.find_one({"user": oldName})
		object_id = itm.get('_id')
		try:
			self.ranking.update({'_id': object_id},
			{"$set": {"user": newName, "frequency":frequency, "wifi":wifi, "public":public}},
			multi=True)
			return True
		except pymongo.errors.DuplicateKeyError:
			return False

	def labInt(self, x):
		return {
    		'Burke Lab':1,
        	'Teherani Lab': 2,
        	'Professor Teherani\'s Lab':2,
        	'Jiang Lab': 3,
        	'Sajda Lab': 4,
        	'Danino Lab': 5
    	}[x]

	def affiliationInt(self, x):
		return {
    		'Student':1,
    		'Professor':2,
    		'Employee':1
    	}[x]

	def getAttributes(self, username, encodeJson=True):
		json_return={
            "username":"username",
            "frequency":0,
            "wifi":True,
            "public":True,
            "lab":0,
            "affiliation":0
		}
		itm = self.ranking.find_one({"user":username})

		json_return["username"] = username
		if (itm == None):
			#print("username not found: " + username)
			if (encodeJson == True):
				return self._encode(json_return, False)
			else:
				return json_return
		json_return["lab"] = self.labInt(itm.get("lab"))
		json_return["affiliation"] = self.affiliationInt(itm.get("affiliation"))
		json_return["frequency"] = itm.get("frequency")
		json_return["wifi"] = itm.get("wifi")
		json_return["public"] = itm.get("public")
		if (encodeJson == True):
			return self._encode(json_return, False)
		else:
			return json_return

	def updateName(self, deviceID, username):
		itm = self.registration_col1.find_one({"screenName": username})
		if (itm is None):
			return False
		self.registration_col1.update({
			"screenName": username
			}, {
			"$set": {
				"userID": deviceID
				}
			}, multi=True)
		return True

	def registerForRankingInfo(self, user, lab, gender, affiliation, frequency=66,wifi=True,public=True):
		self.ranking.insert({
			"user":user,
			"balance":0,
			"lab":lab,
			"gender":gender,
			"affiliation":affiliation,
			"frequency":frequency,
			"wifi":wifi,
			"public":public
			})

	def updateTempBalanceData(self, deviceID, balance):
		self.registration_col1.update({
			"userID": deviceID
			},
			{
			"$set":{
				"tempBalance": balance
				}
			},
			multi=True
			)

	def updateUserBalance(self, deviceID, balance):
		old_balance = self.getUserTempBalance(deviceID)
		self.updateTempBalanceData(deviceID, old_balance + balance)

	def getRankingData(self):
		return self.ranking.find().sort([("balance",-1),("user",1)])

	def getUserTempBalance(self, deviceID):
		U = list(self.registration_col1.find({"userID":deviceID}))
		if (len(U) == 0):
			return None
		doc = U[0]
		return doc["tempBalance"]

	def getUserBalance(self, deviceID):
		U = list(self.registration_col1.find({"userID":deviceID}))
		if (len(U) == 0):
			return None
		doc = U[0]
		return doc["balance"]

	def indirectSensingCollecting(self, applianceID, value):
		self.indirectSensing.insert({
			"applianceID":applianceID,
			"value":value,
			"timestamp":datetime.datetime.utcnow()
			})
	
	def particleSensorCollecting(self, particleSensorNum, PM1L, PM2_5L, PM10L, PM1_0A, PM2_5A, PM10A, um03, um05, um1, um25, um5, um10):
		self.particleSensor.insert({
			"particleSensor":particleSensorNum,
			"PM1":PM1L,
			"PM2":PM2_5L,
			"PM3":PM10L,
			"PM4":PM1_0A,
			"PM5":PM2_5A,
			"PM6":PM10A,
			"um03":um03,
			"um05":um05,
			"um1":um1,
			"um25":um25,
			"um5":um5,
			"um10":um10,
			"timestamp":datetime.datetime.utcnow()
			})	
		
####################################################################
## Machine Learning Functions, for self.suggestionsML ##############
####################################################################

	def submitAcceptedSuggestion(self, deviceID, messageID):
		self.suggestionsML.insert({
			"deviceID":deviceID,
			"messageID":messageID,
			"timestamp":datetime.datetime.utcnow()
			})

####################################################################

	def addLocationSample(self, label, sample):
		return self.dbc.loc_db.sample_col.insert({
			"label":label,
			"sample":sample,
			"timestamp":datetime.datetime.utcnow()
		})

	def getAllLocationSamples(self):
		return list(self.dbc.loc_db.sample_col.find())


	def DestroyLocationSamples(self):
		self.dbc.loc_db.sample_col.remove({})

	def countLocationSamples(self):
		return self.dbc.loc_db.sample_col.count({})
		
#######################################
## Misc Functions - Rishi ##
#######################################
        def getAllUsers(self):
            usernames = []
            users = list(self.registration_col1.find())
            #print users
            for user in users:
                if "name" not in user:
                    continue
                #print "debug", user
                usernames.append(user["name"])
            nameList = ",".join(usernames)
            ret = {
                    "names":usernames
            }
            return self._encode(ret, False)

if __name__ == "__main__":
	dbm=DBMgr(False)
	dbm._TEST()
	## Beware, the _TEST will terminate the script.
