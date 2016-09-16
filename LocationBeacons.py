import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors
from trainingData import training

urls = (
"/","BeaconVals")
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

class generateTrainingData:
    trainingData = []
    trainingLabels = []
    def generate(self):
        rooms = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c", "10F_hallway", "DaninoWetLab"]
        infile = "backup2.txt"
        f = open(infile, 'r')
        x = f.readlines()
        for i in range(len(x)):
            y = x[i].split('\t')
            last = y[-1].split('\n')
            y[-1] = last[0]
            y = map(int, y)
            self.trainingData.append(y)

        infile = "backuplabels2.txt"
        f = open(infile, 'r')
        x = f.readlines()
        for j in range(len(x)):
            y = x[j]
            last = y.split('\n')
            y = last[0]
            self.trainingLabels += [rooms.index(y)]

class BeaconVals:
    trainingDataGenerator = generateTrainingData()
    trainingDataGenerator.generate()
    points = trainingDataGenerator.trainingData
    labels = training.labelNames
    labelNumber = trainingDataGenerator.trainingLabels
    sortedRoomList = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c", "10F_hallway", "DaninoWetLab"]

    def POST(self):

        
        raw_data=web.data()
        locs = raw_data.split(',')
        l = locs[1:]
        ID = locs[0]
        locs = map(int, l)
        KNN = KNearestNeighbors(11, self.points, self.labelNumber)
        location = KNN.classifier(locs)


        #username = cloudserver.db.userIDLookup(ID)
        #if (username is not None):
        #    alpha = username.split('_')
        #    if (len(alpha >= 1)):
        #        if (alpha[0] == "alpha"):
        #            ID = "9432F0A3-660D-4C35-AA63-C7CFDD6D0F4D"
        #            location = cloudserver.db.getUserLocation(ID)
        checkUnknown = False
        for loc in locs:
            if (loc != -100):
                checkUnknown = True
                break
        if (checkUnknown == False):
            unknown_return={
            "location":"Unknown Location",
            "location_id":"Unknown Location",
            "balance":cloudserver.db.getUserBalance(cloudserver.db.userIDLookup(ID)),
            "suggestions":[]
            }
            cloudserver.db.ReportLocationAssociation(ID, None)
            return cloudserver.db._encode(unknown_return,False)

        cloudserver.db.ReportLocationAssociation(ID, self.labels[location])
        moveUsers = cloudserver.SE.moveUsers
        changeScheduleUsers = cloudserver.SE.changeScheduleUsers
        turnOffApplianceUsers = cloudserver.SE.turnOffApplianceUsers
        synchronizeApplianceUsers = cloudserver.SE.synchronizeApplianceUsers
        phantomApplianceUsers = cloudserver.SE.phantomApplianceUsers
        balance_server = cloudserver.db.getUserBalance(cloudserver.db.userIDLookup(ID))

        if (balance_server == False):
            balance_server = 0
        json_return={
            "location":"Location Name",
            "location_id":"locationIDString",
            "balance":balance_server,
            "suggestions":[]
        }

        def make_suggestion_item(iType, iTitle, iBodyText, iReward, messageID, inotification=0, Others={}):
            Others.update({
                "type":iType,
                "title":iTitle,
                "body":iBodyText,
                "reward":iReward,
                "notification":inotification,
                "messageID":messageID
                })
            return Others

        json_return["location_id"]=self.labels[location]
        json_return["location"]=cloudserver.db.RoomIdToName(self.labels[location])
        if (cloudserver.db.userIDLookup(ID) is None):
            print(ID)
            return cloudserver.db._encode(json_return,False)
        print(ID)
        usernameAttributes = cloudserver.db.getAttributes(cloudserver.db.userIDLookup(ID), False)


        #keys = turnOffApplianceUsers.keys()
        #for i in range(len(keys)):
        #    json_return["debug"].append(keys[i])
        if (ID in moveUsers.keys()):
            roomInfo = moveUsers[ID]
            roomId=roomInfo["roomDest"]
            roomName=cloudserver.db.RoomIdToName(roomId)
            messageID = roomInfo["messageID"]

            title="Move to "+roomName
            body="Other people are in " + roomName + ", sharing the room with them can lower everyone's energy footprint. (Don't forget to turn off the lights when you leave!)"
            reward=4
            json_return["suggestions"].append(
                make_suggestion_item("move",title,body,reward, messageID,0, {"to":roomName,"to_id":roomId})
            )

        #json_return["debug"] = turnOffApplianceUsers
        labInt = usernameAttributes["lab"]
        if (ID in turnOffApplianceUsers.keys()):
            applianceList = turnOffApplianceUsers[ID]
            for appliance in applianceList:
                if (not appliance["actionable"]):
                    continue
                room = appliance["rooms"]
                room = room[0]
                if (cloudserver.db.RoomIDToLab(room) != labInt):
                    print("Exception Log: Caught incorrect lab definition {0} {1}".format(cloudserver.db.RoomIDToLab(room), labInt))
                    continue
                applianceID = appliance["id"]
                applianceName = appliance["name"]
                powerUsage = int(appliance["value"])
                messageID = "{0}|{1}|{2}".format("turnoff", ID, applianceID)
                if (powerUsage <= 0):
                    continue
                title="Reduce power of "+applianceName
                body=applianceName+" is consuming excess power (" + str(powerUsage) + " watts), please see if you can switch off some appliance."
                reward=1
                doPush=0
                if(powerUsage>50):
                    #!!TODO: make doPush=1,2,3,4 according to various criteria, not a single threshold.
                    doPush=1
                json_return["suggestions"].append(
                    make_suggestion_item("turnoff",title, body, reward, messageID, doPush, {"appl":applianceName,"appl_id":applianceID, "power":powerUsage}))

        if (ID in phantomApplianceUsers.keys()):
            (phantomRoom, phantomMaxAppliance, phantomMaxPower, phantomRoomLab) = phantomApplianceUsers[ID]
            if (phantomRoomLab != labInt):
                continue
            title = "Power usage in room " + str(phantomRoom) + "is consuming a lot of power"
            body = "Did you forget to turn off " + str(phantomMaxAppliance) + " in " + str(phantomRoom) + "? It is consuming " + str(phantomMaxPower) + "Watts."
            print("Phantom: {0} Suggestion: {1}".format(ID, body))
            reward = 3
            doPush = 1
            messageID = "{0}|{1}|{2}".format("phantom", ID, phantomRoom)
            json_return["suggestions"].append(
                    make_suggestion_item("phantom",title, body, reward, messageID, doPush))
                #applianceID="nwc1003b_c_plug"
                #applianceName=cloudserver.db.ApplIdToName(applianceID)
                #title="Shut off "+applianceName+"?"
                #pwr=cloudserver.db.ApplIdToVal(applianceID)
                #body=applianceName+" is consuming excess power ("+pwr+" watts), please see if you can switch off some appliance."
                #reward=int(0.1*pwr)+1
                #json_return["suggestions"].append(
                #    make_suggestion_item("turnoff",title,body,reward,{"appl":applianceName,"appl_id":applianceID, "power":pwr})
                #    )
        if (ID in changeScheduleUsers.keys()):
            timeshift = changeScheduleUsers[ID]
            if (timeshift == "earlier"):
                messageID = "{0}|{1}|{2}".format("change", ID, "earlier")
                body = "Coming in earlier tomorrow will help to limit excess power usage!"
                reward = 3
                doPush = 0
                json_return["suggestions"].append(
                    make_suggestion_item("change", "Shift schedule 10 minutes earlier", body, reward, messageID, doPush))
            if (timeshift == "later"):
                messageID = "{0}|{1}|{2}".format("change", ID, "later")
                body = "Coming in later tomorrow will help to limit excess power usage!"
                reward = 3
                doPush = 0
                json_return["suggestions"].append(
                    make_suggestion_item("change", "Shift schedule 10 minutes later", body, reward, messageID, doPush))
        
        #filter out message using suggestionIDs
        #Check 1: if display timestamp indicates a recent "dismiss", remove the message entirely.
        #TODO: personalize the interval


        control = cloudserver.db.getControl(ID)
        if (control == True):
            title="Control Group Suggestion"
            body="Control group: There is no energy saving suggestions for this week. Please take your reward!"
            reward=4
            doPush=0
            messageID= "{0}|{1}|{2}".format("controlMessage", ID, "XXXX")
            json_return["suggestions"]=[
                    make_suggestion_item("misc",title, body, reward, messageID, doPush, {})]


        moveInterval=20*60
        applianceInterval=20*60
        changeInterval = 20*60*60
        phantomInterval = 10*60
        miscInterval=60*60*4 #every 4 hours, now for the control message only.

        moveSinceTime=cloudserver.db._now()-moveInterval
        applianceSinceTime=cloudserver.db._now()-applianceInterval
        changeSinceTime = cloudserver.db._now()-changeInterval
        phantomSinceTime = cloudserver.db._now()-phantomInterval
        miscSinceTime=cloudserver.db._now()-miscInterval

        returnList = []
        for item in json_return["suggestions"]:
            if (item["type"] == "move" and cloudserver.db.pushManagementDispCheck(item["messageID"], moveSinceTime)):
                returnList.append(item)
                continue
            if (item["type"] == "turnoff" and cloudserver.db.pushManagementDispCheck(item["messageID"], applianceSinceTime)):
                returnList.append(item)
                continue
            if (item["type"] == "phantom" and cloudserver.db.pushManagementDispCheck(item["messageID"], phantomSinceTime)):
                returnList.append(item)
                continue
            if (item["type"] == "change" and cloudserver.db.pushManagementDispCheck(item["messageID"], changeSinceTime)):
                returnList.append(item)
                continue
            if (item["type"] == "misc" and cloudserver.db.pushManagementDispCheck(item["messageID"], miscSinceTime)):
                returnList.append(item)
                continue

        json_return["suggestions"]=returnList
        userFrequency = usernameAttributes["frequency"]
        #default value = every 4 hours
        pushInterval=60*60*4
        phantomPushInterval = 10*1000000
        if (userFrequency == 0):
            pushInterval = 60*1000000
            phantomPushInterval = 60*1000000
        if (userFrequency == 33):
            pushInterval = 60*60*24
            phantomPushInterval = 10*60
        if (userFrequency == 66):
            pushInterval = 60*60*4
            phantomPushInterval = 10*60
        if (userFrequency == 100):
            pushInterval = 60*30
            phantomPushInterval = 10*60

        #Check 2: if push timeout is too short, erase the push flag.
        #TODO: personalized push interval from DB (notification frequency in config)
         # !!!! TESTINT ONLY ### should be >= than display timeout anyway
        phantomPushSinceTime = cloudserver.db._now()-phantomPushInterval
        pushSinceTime=cloudserver.db._now()-pushInterval
        for i in range(len(json_return["suggestions"])):
            if json_return["suggestions"][i]["notification"]!=0:
                #this is a push message; check if we want to push
                if (json_return["suggestions"][i]["type"] == "phantom"):
                    json_return["suggestions"][i]["type"] = "turnoff"
                    if cloudserver.db.pushManagementPushCheck(messageID, phantomPushSinceTime)==False: #last notification too recent
                    #erase flag
                        json_return["suggestions"][i]["notification"]=0
                    else: #good to go
                        cloudserver.db.pushManagementPushUpdate(messageID)
                messageID=json_return["suggestions"][i]["messageID"]
                if cloudserver.db.pushManagementPushCheck(messageID, pushSinceTime)==False: #last notification too recent
                    #erase flag
                    json_return["suggestions"][i]["notification"]=0
                else: #good to go
                    #remember this push, do not repeat.
                    cloudserver.db.pushManagementPushUpdate(messageID)

        return cloudserver.db._encode(json_return,False)

    def GET(self):
        return 0

Beacons = web.application(urls, locals());
