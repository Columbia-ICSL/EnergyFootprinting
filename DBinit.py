import pymongo
class DBInit(object):
	def _GetConfigValue(self,key):
		try:
			ret=self.config_col.find_one({"_id":key})
			return ret["value"]
		except:
			return None

	def _SetConfigValue(self,key,value):
		self.config_col.replace_one({"_id":key},{"value":value},True)

	def WriteConfigs(self):
		self.ROOM_DEFINITION=[
    {
        "name": "Columbia University",
        "id": "curoot",
        "children": [
            "mudd",
            "nwc"
        ],
        "occupants": {
            "number": 29870,
            "type": "stat"
        }
    },
    {
        "name": "Columbia University/Mudd Building",
        "id": "mudd",
        "children": [],
        "occupants": {
            "number": 2000,
            "type": "stat"
        }
    },
    {
        "name": "Columbia University/Northwest Corner Building",
        "id": "nwc",
        "children": [
            "nwc10"
        ],
        "occupants": {
            "number": 1000,
            "type": "statistics"
        }
    },
    {
        "name": "Columbia University/Northwest Corner Building/Floor 10",
        "id": "nwc10",
        "children": [
            "nwc1000",
            "nwc1008",
            "nwc1003b"
        ],
        "occupants": {
            "number": 0,
            "type": "auto",
            "ids": []
        }
    },
    {
        "name": "Columbia University/Northwest Corner Building/Floor 10/Room 1008",
        "id": "nwc1008",
        "children": [],
        "occupants": {
            "number": 0,
            "type": "auto",
            "ids": []
        }
    },
    {
        "name": "Columbia University/Northwest Corner Building/Floor 10/Room 1000",
        "id": "nwc1000",
        "children": [],
        "occupants": {
            "number": 0,
            "type": "auto",
            "ids": []
        }
    },
    {
        "name": "Columbia University/Northwest Corner Building/Floor 10/Room 1003b",
        "id": "nwc1003b",
        "children": [],
        "occupants": {
            "number": 0,
            "type": "auto",
            "ids": []
        }
    }
]

		self._SetConfigValue("ROOM_DEFINITION",self.ROOM_DEFINITION)

		self.ENERGYDEVICE_DEFINITION={
			"nwc1008_plug1":{
				"type":"plug",
				"room":"nwc1008",
				"seq":1,
				"manufacturer":"AEOTEC by AEON LABS",
				"channel":"SmartThings Hub 2.0"
			},
			"nwc1008_smartvent1":{
				"type":"vent",
				"room":"nwc1008",
				"seq":1,
				"manufacturer":"Keen Home",
				"channel":"SmartThings Hub 2.0"
			},
			"nwc1008_light1":{
				"type":"lightbulb",
				"room":"nwc1008",
				"seq":1,
				"manufacturer":"Cree",
				"channel":"SmartThings Hub 2.0"
			},
			"nwc1003b_plug1":{
				"type":"plug",
				"room":"nwc1003b",
				"seq":1,
				"manufacturer":"AEOTEC by AEON LABS",
				"channel":"SmartThings Hub 2.0"
			},
			"nwc1003b_plug2":{
				"type":"plug",
				"room":"nwc1003b",
				"seq":2,
				"manufacturer":"AEOTEC by AEON LABS",
				"channel":"SmartThings Hub 2.0"
			}
		}
		self._SetConfigValue("ENERGYDEVICE_DEFINITION",self.ENERGYDEVICE_DEFINITION)

	def __init__(self):
		self.name="DB Initialization"
		print self.name
		self.dbc=pymongo.MongoClient()
		self.config_col=self.dbc.db.config
		self.WriteConfigs()

a=DBInit()
