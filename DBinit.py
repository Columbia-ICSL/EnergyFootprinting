import re
import pymongo

PUBLIC_SPACE = 0
BURKE_LAB = 1
TEHERANI_LAB = 2
JIANG_LAB = 3
SAJDA_LAB = 4
DANINO_LAB = 5
OFFICE_SPACE = 0
STUDENT_WORK_SPACE = 1
GENERAL_SPACE = 2
WINDOWED = True
NOT_WINDOWED = False
ACTIONABLE = True
NOT_ACTIONABLE = False
DUTY_CYCLE = True
NO_DUTY_CYCLE = False

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
        def addRoom(id, name, coord, labDefinition, spaceDefinition, windowedDefinition):
            self.ROOM_DEFINITION+=[{
                "id":id,
                "name":name,
                "coordinate": coord,
                "lab": labDefinition,
                "space": spaceDefinition,
                "windowed": windowedDefinition
            }]
        addRoom("10F_hallway", "NWC 10F Hallway", [0,0], PUBLIC_SPACE, GENERAL_SPACE, NOT_WINDOWED)
        addRoom("DaninoWetLab", "Danino Wet Lab Space", [0, 0], DANINO_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc10","NWC 10F Public Area", [40.810174, -73.962006], PUBLIC_SPACE, GENERAL_SPACE, NOT_WINDOWED) # public area 10F, elevator bank etc.
        addRoom("nwc10m","NWC 10M Public Area", [40.810174, -73.962006], PUBLIC_SPACE, GENERAL_SPACE, NOT_WINDOWED) # public area 10F, elevator bank etc.
        # exits
        addRoom("nwc8","NWC 8F Public Area", [40.810174, -73.962006], PUBLIC_SPACE, GENERAL_SPACE, WINDOWED) # public area 8F
        addRoom("nwc7","NWC 7F Public Area", [40.810174, -73.962006], PUBLIC_SPACE, GENERAL_SPACE, WINDOWED)# public area 7F
        addRoom("nwc4","NWC 4F Public Area", [40.810174, -73.962006], PUBLIC_SPACE, GENERAL_SPACE, WINDOWED) # public area 4F

        # 10F space units
        addRoom("nwc1008","NWC 1008 Office", [40.809997, -73.961983], JIANG_LAB, OFFICE_SPACE, WINDOWED)
        addRoom("nwc1006","NWC 1006 Office", [40.809997, -73.961983], BURKE_LAB, OFFICE_SPACE, WINDOWED)
        addRoom("nwc1007","NWC 1007 Office", [40.809997, -73.961983], TEHERANI_LAB, OFFICE_SPACE, WINDOWED)
        addRoom("nwc1009","NWC 1009 Office", [40.809997, -73.961983], PUBLIC_SPACE, OFFICE_SPACE, WINDOWED)
        addRoom("nwc1010","NWC 1010 Office", [40.809997, -73.961983], SAJDA_LAB, OFFICE_SPACE, WINDOWED)

        addRoom("nwc1003g","1003 Optics G Lab", [40.809965, -73.962063], JIANG_LAB, STUDENT_WORK_SPACE, NOT_WINDOWED)
        #addRoom("nwc1003b","1003B Lab",[40.810022, -73.962075])
        addRoom("nwc1003b_a","1003B Lab Area A",[40.809980, -73.962159], JIANG_LAB, STUDENT_WORK_SPACE, WINDOWED) # Seat for Peter/Daniel
        addRoom("nwc1003b_b","1003B Lab Area B",[40.809947, -73.962050], JIANG_LAB, STUDENT_WORK_SPACE, WINDOWED) # Seat for Danny/Stephen
        addRoom("nwc1003b_c","1003B Lab Area C",[40.810005, -73.962072], JIANG_LAB, STUDENT_WORK_SPACE, WINDOWED) # Seat for Rishi
        addRoom("nwc1003b_t","1003B Teherani Lab",[40.809897, -73.962138], TEHERANI_LAB, STUDENT_WORK_SPACE, WINDOWED) # Prof. Teherani's space


        # 10M space units, aisle 1-8
        addRoom("nwc1000m_a1","10M Floor, Aisle 1", [40.810050, -73.961945], BURKE_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a2","10M Floor, Aisle 2", [40.810038, -73.961955], BURKE_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a3","10M Floor, Aisle 3", [40.810021, -73.961966], DANINO_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a4","10M Floor, Aisle 4", [40.810005, -73.961978], DANINO_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a5","10M Floor, Aisle 5", [40.809986, -73.961991], TEHERANI_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a6","10M Floor, Aisle 6", [40.809968, -73.962003], JIANG_LAB, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a7","10M Floor, Aisle 7", [40.809950, -73.962017], PUBLIC_SPACE, STUDENT_WORK_SPACE, WINDOWED)
        addRoom("nwc1000m_a8","10M Floor, Aisle 8", [40.809933, -73.962030], PUBLIC_SPACE, STUDENT_WORK_SPACE, WINDOWED)

        # Only the lowest-layer cubicles, corresponding to localization unit

        self._SetConfigValue("ROOM_DEFINITION",self.ROOM_DEFINITION)

        self.APPLIANCE_DEFINITION=[]
        def addAppliance(Id, Name, Type, roomsRegex, actionableDefinition, dutyCycleDefinition):
            roomsMatched=[]
            for room in self.ROOM_DEFINITION:
                if re.search(roomsRegex, room["id"]):
                    roomsMatched+=[room["id"]]
            item={
                "id":Id,
                "name":Name,
                "type":Type,
                "rooms":roomsMatched,
                "actionable": actionableDefinition,
                "dutyCycle": dutyCycleDefinition
            }
            self.APPLIANCE_DEFINITION+=[item]

        addAppliance("nwc1007_plug1", "Plug#1 in Prof Teherani's Office", "Electrical", "nwc1007", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1007_plug2", "Plug#2 in Prof Teherani's Office", "Electrical", "nwc1007", ACTIONABLE, NO_DUTY_CYCLE)

        addAppliance("nwc1008_plug1", "Plug#1 in Prof Jiang's Office", "Electrical", "nwc1008", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1008_smartvent1", "SmartVent in Prof Jiang's Office (HVAC Indirect Sensing)", "HVAC", "nwc1008", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1008_light", "Lights in Prof Jiang's Office", "Light", "nwc1008", ACTIONABLE, NO_DUTY_CYCLE)

        addAppliance("nwc1003b_a_plug", "Plugmeter in 1003B Lab Area A (Peter)", "Electrical", "nwc1003b_a", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1003b_b_plug", "Plugmeter in 1003B Lab Area B (Danny&Stephen)", "Electrical", "nwc1003b_b", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1003b_c_plug", "Plugmeter in 1003B Lab Area C (Rishi)", "Electrical", "nwc1003b_c", ACTIONABLE, NO_DUTY_CYCLE)
        
        addAppliance("nwc1003b_fin", "Fin Tube Radiator in 1003B", "HVAC", "nwc1003b.*", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1003b_vav", "Air Vent in 1003B", "HVAC", "nwc1003b.*", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1003b_lex", "Fume Hoods in 1003B", "HVAC", "nwc1003b.*", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc10_ahu", "Air Intake System for 10F", "HVAC", "nwc10.*", ACTIONABLE, NO_DUTY_CYCLE)
        # TODO: Map the FCUs (Fan Coils) to rooms, given floor plan
        addAppliance("nwc1003g_vav", "Air Vent in 1003G", "HVAC", "nwc1003g.*", ACTIONABLE, NO_DUTY_CYCLE)
        
        addAppliance("nwc1003g_plug1", "Plugmeter in 1003G (Printer&Computer)", "Electrical", "nwc1003g", ACTIONABLE, DUTY_CYCLE)
        addAppliance("nwc1003g_plug2", "Plugmeter in 1003G (Soldering Station)", "Electrical", "nwc1003g", ACTIONABLE, DUTY_CYCLE)
        addAppliance("nwc1003g_plug3", "Plugmeter in 1003G (Projector&XBox)", "Electrical", "nwc1003g", ACTIONABLE, DUTY_CYCLE)
        addAppliance("nwc1003b_light", "Lights in 1003B Lab", "Light", "nwc1003b.*", ACTIONABLE, NO_DUTY_CYCLE)
        addAppliance("nwc1003g_light", "Lights in 1003G Lab", "Light", "nwc1003g", ACTIONABLE, NO_DUTY_CYCLE)

        for a in range(1,9,1):#1..8
            for p in range(1,3,1):#1..2
                addAppliance("nwc1000m_a"+str(a)+"_plug"+str(p), "Power strip #"+str(p)+" in Mezzaine Level, Aisle #"+str(a), "Electrical", "nwc1000m_a"+str(a), ACTIONABLE, NO_DUTY_CYCLE)
        
        addAppliance("nwc1000m_light", "Shared Lighting in Mezzaine Level", "Light", "nwc1000m_.*", NOT_ACTIONABLE, NO_DUTY_CYCLE)

        self._SetConfigValue("APPLIANCE_DEFINITION",self.APPLIANCE_DEFINITION)

        # Snapshot timeout, in seconds
        self._SetConfigValue("SAMPLING_TIMEOUT_SHORTEST", 6)
        self._SetConfigValue("SAMPLING_TIMEOUT_LONGEST", 60*2)

        self._SetConfigValue("WATCHDOG_TIMEOUT_USER", 60*10)
        self._SetConfigValue("WATCHDOG_TIMEOUT_APPLIANCE", 60*20)


    def __init__(self):
        self.name="DB Initialization"
        print(self.name)
        self.dbc=pymongo.MongoClient()
        self.config_col=self.dbc.db.config
        self.WriteConfigs()
        print(self._GetConfigValue("APPLIANCE_DEFINITION"))

DBInit()
