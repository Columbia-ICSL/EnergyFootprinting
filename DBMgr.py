import pymongo
import datetime

class DBMgr(object):

	def __init__(self):
		self.timeout=900
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.engcol=self.dbc.db.energy_logs
		self.poscol=self.dbc.db.position_logs
		self.raw_data=self.dbc.db.raw_data_logs
		#self.pwrcol=self.dbc.db.realtime_pwr

	def _time(self,timestamp=0):
		if timestamp==0:
			return datetime.datetime.utcnow()
		else:
			return datetime.datetime.utcfromtimestamp(timestamp)

	def SavePlug(self,room,description,kwhs,watts,timestamp=0):
		e_doc = {
			"room": room,
			"energy": kwhs,
			"timestamp": self._time(timestamp),
			"occupants": [],
			"description": description
			}

		raw_data = {
			"room":room,
			"description":description,
			"timestamp": self._time(timestamp),
			"type":"Plug",
			"data":{
				"power":watts,
				"energy":kwhs
				}
			}

		return [
			self.engcol.insert_one(e_doc),
			self.raw_data.insert_one(raw_data)
			]
		
	def SaveHVAC(self,room,description,temp,pres,timestamp=0):
		kwhs= pres*2.1444 #arbitraty
		e_doc = {
			"room": room,
			"energy": kwhs,
			"timestamp": self._time(timestamp),
			"occupants": [],
			"description": description
			}

		raw_data = {
			"room":room,
			"description":description,
			"timestamp": self._time(timestamp),
			"type":"HVAC_Approximation",
			"data":{
				"temperature":temp,
				"pressure":pres
				}
			}

		return [
			self.engcol.insert_one(e_doc),
			self.raw_data.insert_one(raw_data)
			]


	def SavePosition(self,person,room,timestamp=0,since=False):
		if since!=False:
			since=self._time(since)
		else:
			since=self._time(timestamp)+datetime.timedelta(seconds=-self.timeout)

		doc = {
			"person": person,
			"room": room,
			"timestamp": self._time(timestamp)
		}
		id=self.poscol.insert_one(doc).inserted_id

		condition = {
			"room":room,
			"timestamp":{
				"$gte":since,
				"$lt":self._time(timestamp)
			}
		}
		action = {
			"$addToSet"	:{
				"occupants" : person
			}
		}
		#for post in posts.find(condition):
		self.engcol.update_many(condition,action)
		return id

	def QueryRoom(self,room,start,end):
		result=[]
		condition = {
			"room":room,
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}

		for log in self.engcol.find(condition).sort([
    			("timestamp", pymongo.DESCENDING)
			]):
			result+=[log]
		return result

	def QueryPerson(self,person,start,end):
		result=[]
		condition = {
			"occupants":person,
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}

		for log in self.engcol.find(condition):
			log["value"]=log["energy"]/len(log["occupants"])
			result+=[log]
		return result
		#add the "value" value from all array items, to get total energy
