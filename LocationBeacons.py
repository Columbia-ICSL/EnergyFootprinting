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
    KNN = KNearestNeighbors(3, points, labelNumber)
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
        data = "data="
        for user in moveUsers:
            if (ID == user):
                data += "MO,"
                data += cloudserver.SE.roomOccupancySnapshot
                break
        #for user in changeScheduleUsers:
            #if (ID == user):
                #data += "CS,"
                #data += cloudserver.SE.roomOccupancySnapshot
                #break
        for user in turnOffApplianceUsers:
            if (ID == user):
                data += "TO,"
                data += cloudserver.SE.roomOccupancySnapshot
                break
        #for user in synchronizeApplianceUsers:
            #if (ID == user):
                #data += "SA,"
                #data += cloudserver.SE.roomOccupancySnapshot
                #break
        return data

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

Beacons = web.application(urls, locals());
