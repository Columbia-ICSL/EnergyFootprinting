import pymongo
import datetime
import time
import calendar
from bson import ObjectId

class DBMgr(object):

	def __init__(self):
		self.T=900
		self.name="DB Manager"
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
		#(room, PULLcallbackURL, latestUpdate)

	def _time(self,timestamp=0):
		if timestamp==0:
			return datetime.datetime.utcnow()
		else:
			return datetime.datetime.utcfromtimestamp(timestamp)
	
	def _T(self, timestamp):
		if timestamp==0:
			return _TforDatetime(datetime.datetime.utcnow())
		return int(timestamp/self.T)
	def _TforDatetime(self, datetime):
		utc_seconds = calendar.timegm(datetime.utctimetuple())
		return self._T(utc_seconds)

	def __add_energy_event(self,room,timestamp,description,val_in_kwh):
		e_doc = {
			"room": room,
			"energy": val_in_kwh,
			"timestamp": self._time(timestamp),
			#"occupants": [],
			"description": description
			}
		ID=self.engcol.insert(e_doc)
		#should consider repeated insertion? or two same description may be intentional??
		T=self._T(timestamp)

		locator={"room":room,"T":T}
		current_doc=self.stdcol.find_one(locator)
		if current_doc==None:
			current_doc={
				"room":room, "T":T,
				"value":0,"consumption":[],
				"occupants":[],
				"responsibility":[]
			}

		current_doc["consumption"] += [ str(ID) ]
		current_doc["value"] += val_in_kwh
		self.stdcol.replace_one(locator,current_doc,True)#upsert=true
		return current_doc

	def __maintenance_responsibility(self,room,T):
		nowT=self._TforDatetime(self._time(0))
		cond={"room":room,"T":T}
		item=self.stdcol.find_one(cond)
		if item==None:
			return False
		if len(item["occupants"])==0:
			if T>=nowT:
				return
			#if no people and T in past, inherit!
			#!!!TODO find nonempty occ list in the past, update
			latest_w_occ=self.stdcol.find_one(
				{
					"room":room,
					"T":{"$lt":T},
					"occupants": {"$not": {"$size": 0}}
				},
				sort=[
    			("T", pymongo.DESCENDING)
			])
			#modified item
			update_resp=latest_w_occ["occupants"]
		else:
			update_resp=item["occupants"]
		update_act={
			"$set":{
				"responsibility":update_resp
			}
		}
		return self.stdcol.update_one(cond,update_act)

	def __maintenance_responsibilities(self,T=0):
		if T==0:
			nowT=self._TforDatetime(self._time(0))
			T=nowT-1

		#iterate every room with T==T
		#loop T==last..currT-1?
		return

	def __add_occupant_T(self,room,person,T):
		#addToSet
		cond={"room":room,"T":T}
		if self.stdcol.find_one(cond)==None:
			current_doc={
				"room":room, "T":T,
				"value":0,"consumption":[],
				"occupants":[],
				"responsibility":[]
			}
			self.stdcol.insert_one(current_doc)

		act = {
			"$addToSet"	:{
				"occupants" : person
			}
		}
		id=self.stdcol.update_one(cond,act,True)
		self.__maintenance_responsibility(room,T)
		return id

	def __add_location_event(self,person,room,confidence,timestamp):
		
		doc = {
			"person": person,
			"room": room,
			"confidence":confidence,
			"timestamp": self._time(timestamp)
		}
		id=self.poscol.insert_one(doc).inserted_id
		T=self._T(timestamp)
		self.__add_occupant_T(room,person,T)
		return id

	def __query_room_history(self,room,Tl,Tu): #lower/upper bounds
		cond={
			"room":room, 
			"T":{
				"$gte":Tl,
				"$lte":Tu
			}
		}
		ret= list(self.stdcol.find(cond))
		return ret
	def __query_room_by_timestamp(self,person,time1,time2):
			#!!TODO: remove/filter illegitimate incidents in first and last block??
		return self.__query_room_history(room,self._T(time1),self._T(time2))


	def __query_person_history(self,person,Tl,Tu): #lower/upper bounds
		cond={
			"responsibility":person, 
			"T":{
				"$gte":Tl,
				"$lte":Tu
			}
		}
		ret= list(self.stdcol.find(cond))
		return ret
	def __query_person_history_full(self,person,Tl,Tu):
	#expand all consumption incidents
		history=self.__query_person_history(person,Tl,Tu)
		ret=[]
		for item in history:
			rate=1.0 / len(item["responsibility"])
			for ID in item["consumption"]:
				actual_item=self.engcol.find_one({"_id":ObjectId(ID)})
				actual_item["value"]=actual_item["energy"] * rate
			ret+=[actual_item]
		return ret

	def __query_person_by_timestamp(self,person,time1,time2):
			#!!TODO: remove/filter illegitimate incidents in first and last block??
		return self.__query_person_history_full(person,self._T(time1),self._T(time2))

	def _TEST(self):
		self.stdcol=self.dbc.db.test_col
		self.stdcol.remove()
		#self.__TEST()
		self.__add_energy_event("1008",12*900+1,"test1",1.3)
		self.__add_energy_event("1008",13*900+1,"test1",1.5)
		self.__add_energy_event("1008",14*900+1,"test1",2.3)
		self.__add_energy_event("1008",15*900+1,"test1",2.3)
		self.__add_location_event("personA","1008","0.9",12*900+5)
		self.__add_location_event("personB","1008","0.9",13*900+5)
		self.__add_location_event("personB","1008","0.9",16*900+1)
		self.__add_location_event("personC","1008","0.9",16*900+1)

		self.__add_energy_event("1008",16*900+1,"TEST2",44)

		self.__maintenance_responsibility("1008",12)
		self.__maintenance_responsibility("1008",13)
		self.__maintenance_responsibility("1008",15)
		res= self.stdcol.find_one({"room":"1008","T":15})
		assert(res["responsibility"]==["personB"])
		res=self.__query_person_by_timestamp("personB",12*900,16*900)
		assert(len(res)==3)
		assert(res[2]["description"]=="TEST2")
		assert(res[2]["value"]==44/2)

		print "Test Success."
		self.stdcol.remove()

	def SavePlug(self,room,description,kwhs,watts,timestamp=0):
		return self.__add_energy_event(room,timestamp,"Plug:"+description+" currW:"+str(watts),kwhs)		
	
	def SaveHVAC(self,room,description,temp,pres,timestamp=0):
		kwhs= pres*2.1444 #arbitraty
		return self.__add_energy_event(room,timestamp,"HVAC:"+description+" currPres:"+str(pres)+" currTemp:"+str(temp),kwhs)		

#	def CheckLocation(self,person):
#		return ret
	
	def SaveLocation(self,person,room,confidence,timestamp=0):
		return self.__add_location_event(person,room,confidence,timestamp)


	def QueryRoom(self,room,start,end):
		return __query_room_by_timestamp(room,start,end)

	def QueryPerson(self,person,start,end):
		return __query_person_by_timestamp(person,start,end)
		#add the "value" value from all array items, to get total energy

if __name__ == "__main__":
	db=DBMgr()
	db._TEST()