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
        }
        def make_suggestion_item(iType, iTitle, iBodyText, iReward, Others={}):
            Others.update({
                "type":iType,
                "title":iTitle,
                "body":iBodyText,
                "reward":iReward,
                })
            return Others

        json_return["location_id"]=self.labels[location]
        json_return["location"]=cloudserver.db.RoomIdToName(self.labels[location])
        for user in moveUsers:
            if (ID == user):
                roomId="nwc1008"
                roomName=cloudserver.db.RoomIdToName(roomId)
                title="Move to "+roomName
                body="Please consider sharing the room to lower everyone's energy footprint."
                reward=4
                json_return["suggestions"].append(
                    make_suggestion_item("move",title,body,reward,{"to":roomName,"to_id":roomId})
                    )
                break

        for user in turnOffApplianceUsers:
            if (ID == user):
                applianceList = turnOffApplianceUsers[user]
                for appliance in applianceList:
                    applianceID = appliance["id"]
                    applianceName = appliance["name"]
                    powerUsage = appliance["value"]
                    title="Shut off "+applianceName
                    body=applianceName+" is consuming excess power ( watts), please see if you can switch off some appliance."
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
