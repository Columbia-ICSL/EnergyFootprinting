import re
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
        self.ROOM_DEFINITION=[]
        def addRoom(id, name, coord):
            self.ROOM_DEFINITION+=[{
                "id":id,
                "name":name,
                "coordinate": coord,
            }]
        
        addRoom("nwc1008","NWC 1008 Office", [40.809997, -73.961983])
        addRoom("nwc1003g","1003 Optics G Lab", [40.809965, -73.962063])
        addRoom("nwc1003b","1003B Lab",[40.810022, -73.962075])
        
        addRoom("nwc1000m_a1","10M Floor Aisle 1", [40.810050, -73.961945])
        addRoom("nwc1000m_a2","10M Floor Aisle 2", [40.810038, -73.961955])
        addRoom("nwc1000m_a3","10M Floor Aisle 3", [40.810021, -73.961966])
        addRoom("nwc1000m_a4","10M Floor Aisle 4", [40.810005, -73.961978])
        addRoom("nwc1000m_a5","10M Floor Aisle 5", [40.809986, -73.961991])
        addRoom("nwc1000m_a6","10M Floor Aisle 6", [40.809968, -73.962003])
        addRoom("nwc1000m_a7","10M Floor Aisle 7", [40.809950, -73.962017])
        addRoom("nwc1000m_a8","10M Floor Aisle 8", [40.809933, -73.962030])

        # Only the lowest-layer cubicles, corresponding to localization unit

        self._SetConfigValue("ROOM_DEFINITION",self.ROOM_DEFINITION)

        self.APPLIANCE_DEFINITION=[]
        def addAppliance(id, type, roomsRegex):
            roomsMatched=[]
            for room in self.ROOM_DEFINITION:
                if re.search(roomsRegex, room["id"]):
                    roomsMatched+=[room["id"]]
            item={
                "id":id,
                "type":type,
                "rooms":roomsMatched,
            }
            self.APPLIANCE_DEFINITION+=[item]

        addAppliance("nwc1008_plug1", "Electrical", "nwc1008")
        addAppliance("nwc1008_smartvent1", "HVAC", "nwc1008")
        addAppliance("nwc1008_light", "Light", "nwc1008")

        addAppliance("nwc1003b_plug1", "Electrical", "nwc1003b")
        addAppliance("nwc1003b_plug2", "Electrical", "nwc1003b")
        addAppliance("nwc1003g_plug1", "Electrical", "nwc1003g")
        addAppliance("nwc1003g_plug2", "Electrical", "nwc1003g")
        addAppliance("nwc1003b_light", "Light", "nwc1003b")
        addAppliance("nwc1003g_light", "Light", "nwc1003g")

        addAppliance("nwc1000m_a1_plug", "Electrical", "nwc1000m_a1")
        addAppliance("nwc1000m_a2_plug", "Electrical", "nwc1000m_a2")
        addAppliance("nwc1000m_a3_plug", "Electrical", "nwc1000m_a3")
        addAppliance("nwc1000m_a4_plug", "Electrical", "nwc1000m_a4")
        addAppliance("nwc1000m_a5_plug", "Electrical", "nwc1000m_a5")
        addAppliance("nwc1000m_a6_plug", "Electrical", "nwc1000m_a6")
        addAppliance("nwc1000m_a7_plug", "Electrical", "nwc1000m_a7")
        addAppliance("nwc1000m_a8_plug", "Electrical", "nwc1000m_a8")

        addAppliance("nwc1000m_light", "Light", "nwc1000m_.*")

        self._SetConfigValue("APPLIANCE_DEFINITION",self.APPLIANCE_DEFINITION)

        # Snapshot timeout, in seconds
        self._SetConfigValue("SAMPLING_TIMEOUT_SHORTEST", 6)
        self._SetConfigValue("SAMPLING_TIMEOUT_LONGEST", 60*2)

    def __init__(self):
        self.name="DB Initialization"
        print(self.name)
        self.dbc=pymongo.MongoClient()
        self.config_col=self.dbc.db.config
        self.WriteConfigs()
        print(self._GetConfigValue("APPLIANCE_DEFINITION"))

DBInit()
