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

        locs = map(int, l)
        location = self.KNN.classifier(locs)
        cloudserver.db.SaveLocationData(0, self.labels[location[0]])
        return "1 2 3 1 4"

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

Beacons = web.application(urls, locals());
