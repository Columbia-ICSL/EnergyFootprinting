import pymongo
import datetime

class DBMgr(object):

	def __init__(self):
		self.timeout=900
		self.name="DB Manager"
		self.dbc=pymongo.MongoClient()
		self.engcol=self.dbc.db.energy_logs
		self.poscol=self.dbc.db.position_logs
		self.pwrcol=self.dbc.db.realtime_pwr

<<<<<<< HEAD
	def _time(self,timestamp=0):
=======
	def SaveEnergy(self,room,description,energy,watts,timestamp=0):
>>>>>>> cd5de5d825507c2983397dc07e85b12eee57b617
		if timestamp==0:
			return datetime.datetime.utcnow()
		else:
			return datetime.datetime.utcfromtimestamp(timestamp)

	def SaveEnergyPower(self,room,description,watts,kwhs,timestamp=0):
		e_doc = {
			"room": room,
<<<<<<< HEAD
			"energy": kwhs,
			"timestamp": self._time(timestamp),
=======
			"energy": energy,
			"power":watts,
			"timestamp": timestamp,
>>>>>>> cd5de5d825507c2983397dc07e85b12eee57b617
			"occupants": [],
			"description": description
			}	
		p_cond = {
			"room": room,
			"description": description
		}
		p_doc = {
			"room": room,
			"power": kwhs,
			"timestamp": self._time(timestamp),
			"occupants": {},
			"description": description
			}

		return [
			self.engcol.insert_one(e_doc).inserted_id,
			self.pwrcol.update(p_cond,p_doc,True)
			]
		#Note: the pwr update doesn't consider timestamp sequence!!
		# client should always report data using timed sequence, otherwise server should compare timestamp before updating.



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
		condition = {
			"room":room 
			#not considering timestamp freshness!
		}
		action = {
			"$set"	:{
				"occupants."+person:self._time(timestamp)
			}
		}
		self.pwrcol.update_many(condition,action)
		return id


	def QueryRealtime(self,room,description=False):
		condition = {
			"room":room
		}
		since=self._time(0)+datetime.timedelta(seconds=-self.timeout)

		if description:
			condition["description"]=description
		query=self.pwrcol.find(condition)

		ret=[]
		for roomitem in query:
			#check roomitem.occupants
			#for k, v in roomitem.occupants.iteritems():
    		#if v<since:
        	#	del roomitem.occupants[k]
        	#save the updates too?
			ret+=[roomitem]
		return ret



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

	def QueryPersonRealtime(self,person):
		since=self._time(0)+datetime.timedelta(seconds=-self.timeout)
		condition = {
			"occupants."+person: {
				"$gte":since
			}
		}
		
		query=self.pwrcol.find(condition)

		ret=[]
		for pwritem in query:
			#timestamp sanitation!!!
			pwritem['value']=pwritem['power']/len(pwritem['occupants'])
			ret+=[pwritem]
		return ret
