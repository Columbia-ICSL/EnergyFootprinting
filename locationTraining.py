import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors
from trainingData import training

urls = (
"/","train")

class train:
    points = training.datapoints
    labels = training.labelNames
    labelNumber = training.labelNumber
    KNN = KNearestNeighbors(3, points, labelNumber)
    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')
        l = locs[1:]

        if (locs[0] == "GET"):
            locs = map(int, l)
            KNN = KNearestNeighbors(3, cloudServer.trainingData, cloudServer.trainingLabels)
            location = self.KNN.classifier(locs)
            return location
        
        ID = locs[0]
        intID = int(ID)
        locs = map(int, l)
        cloudServer.trainingData.append(locs)
        cloudServer.trainingLabels.append(intID)
        location = self.KNN.classifier(locs)
        return data

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

locationTraining = web.application(urls, locals());
