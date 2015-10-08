import pymongo
import datetime

class DBMgr(object):

	def __init__(self):
		self.timeout=900
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.col=self.dbc.db.energy_logs
		self.poscol=self.dbc.db.position_logs

	def SaveEnergy(self,room,description,energy,watts,timestamp=0):
		if timestamp==0:
			timestamp=datetime.datetime.utcnow()
		else:
			timestamp=datetime.datetime.utcfromtimestamp(timestamp)

		doc = {
			"room": room,
			"energy": energy,
			"power":watts,
			"timestamp": timestamp,
			"occupants": [],
			"description": description
			}
		return self.col.insert_one(doc).inserted_id

	def SavePosition(self,person,room,timestamp=0):
		if timestamp==0:
			timestamp=datetime.datetime.utcnow()
		else:
			timestamp=datetime.datetime.utcfromtimestamp(timestamp)
		prev_time=timestamp+datetime.timedelta(seconds=-self.timeout)

		doc = {
			"person": person,
			"room": room,
			"timestamp": timestamp
		}
		id=self.poscol.insert_one(doc).inserted_id

		condition = {
			"room":room,
			"timestamp":{
				"$gte":prev_time,
				"$lt":timestamp
			}
		}
		action = {
			"$addToSet"	:{
				"occupants" : person
			}
		}
		#for post in posts.find(condition):
		self.col.update(condition,action,{"multi":True})
		return id

	def QueryRealtime(self,room):
		timestamp=datetime.datetime.utcnow()
		prev_time=timestamp+datetime.timedelta(seconds=-self.timeout)

		condition = {
			"room":room,
			"timestamp":{
				"$gte":prev_time,
				"$lt":timestamp
			}
		}
		return self.col.find(condition)

	def QueryPerson(self,person,start,end):
		result=[]
		condition = {
			"occupants":person,
			"timestamp":{
				"$gte":datetime.datetime.utcfromtimestamp(start),
				"$lt":datetime.datetime.utcfromtimestamp(end)
			}
		}

		for log in self.col.find(condition):
			log["value"]=log["energy"]/len(log["occupants"])
			result+=[log]
		return result
		#add the "value" value from all array items, to get total energy

	def QueryPersonRecent(self,person):
		s=(datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds()
		return self.QueryPerson(person,s-900,s)
