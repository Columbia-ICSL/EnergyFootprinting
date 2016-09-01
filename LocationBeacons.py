import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors
from trainingData import training

urls = (
"/","BeaconVals")

class BeaconVals:
    points = training.datapoints
    labels = training.labelNames
    labelNumber = training.labelNumber
    KNN = KNearestNeighbors(11, points, labelNumber)
    sortedRoomList = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c"]

    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')
        l = locs[1:]
        ID = locs[0]
        locs = map(int, l)
        location = self.KNN.classifier(locs)
        cloudserver.db.ReportLocationAssociation(ID, self.labels[location])
        cloudserver.db.SaveLocationData(0, self.labels[location])
        moveUsers = cloudserver.SE.moveUsers
        changeScheduleUsers = cloudserver.SE.changeScheduleUsers
        turnOffApplianceUsers = cloudserver.SE.turnOffApplianceUsers
        synchronizeApplianceUsers = cloudserver.SE.synchronizeApplianceUsers
        balance_server = cloudserver.db.getUserBalance(cloudserver.db.userIDLookup(ID))
        if (balance_server == False):
            balance_server = 0
        json_return={
            "location":"Location Name",
            "location_id":"locationIDString",
            "balance":balance_server,
            "suggestions":[],
            "debug":[]
        }
        def make_suggestion_item(iType, iTitle, iBodyText, iReward, Others={}):
            Others.update({
                "type":iType,
                "title":iTitle,
                "body":iBodyText,
                "reward":iReward,
                "notification":0
                })
            return Others

        json_return["location_id"]=self.labels[location]
        json_return["location"]=cloudserver.db.RoomIdToName(self.labels[location])
        keys = turnOffApplianceUsers.keys()
        for i in range(len(keys)):
            json_return["debug"] = keys[i]
        if (ID in moveUsers.keys()):
            roomInfo = moveUsers[ID]
            roomId=roomInfo["roomDest"]
            roomName=cloudserver.db.RoomIdToName(roomId)
            title="Move to "+roomName
            body="Please consider sharing the room to lower everyone's energy footprint."
            reward=4
            json_return["suggestions"].append(
                make_suggestion_item("move",title,body,reward,{"to":roomName,"to_id":roomId})
            )

        if (ID in turnOffApplianceUsers.keys()):
            applianceList = turnOffApplianceUsers[ID]
            for appliance in applianceList:
                applianceID = appliance["id"]
                applianceName = appliance["name"]
                powerUsage = appliance["value"]
                #if (powerUsage < 10):
                #    continue
                title="Shut off "+applianceName
                body=applianceName+" is consuming excess power (" + str(powerUsage) + " watts), please see if you can switch off some appliance."
                reward=1
                json_return["suggestions"].append(
                    make_suggestion_item("turnoff",title, body, reward, {"appl":applianceName,"appl_id":applianceID, "power":powerUsage}))





                #applianceID="nwc1003b_c_plug"
                #applianceName=cloudserver.db.ApplIdToName(applianceID)
                #title="Shut off "+applianceName+"?"
                #pwr=cloudserver.db.ApplIdToVal(applianceID)
                #body=applianceName+" is consuming excess power ("+pwr+" watts), please see if you can switch off some appliance."
                #reward=int(0.1*pwr)+1
                #json_return["suggestions"].append(
                #    make_suggestion_item("turnoff",title,body,reward,{"appl":applianceName,"appl_id":applianceID, "power":pwr})
                #    )

        return cloudserver.db._encode(json_return,False)

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

Beacons = web.application(urls, locals());
