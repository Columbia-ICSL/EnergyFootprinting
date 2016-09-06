import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors
from trainingData import training
from LocationBeacons import BeaconVals
urls = (
"/","train")

class train:
    points = training.datapoints
    labels = training.labelNames
    labelNumber = training.labelNumber
    K = 11
    KNN = KNearestNeighbors(3, points, labelNumber)
    rooms = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c"]
    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')

        if (locs[0] == "REUP"):
            infile = "backup2.txt"
            f = open(infile, 'r')
            x = f.readlines()
            BeaconVals.points = []
            for i in range(len(x)):
                y = x[i].split('\t')
                last = y[-1].split('\n')
                y[-1] = last[0]
                y = map(int, y)
                BeaconVals.points.append(y)
            infile = "backuplabels2.txt"
            f = open(infile, 'r')
            x = f.readlines()
            BeaconVals.labelNumber = []
            for j in range(len(x)):
                y = x[j]
                last = y.split('\n')
                y = last[0]

                BeaconVals.labelNumber += [self.rooms.index(y)]               
            return "successful reupload"
        if (locs[0] == "DES"):
            BeaconVals.points = []
            BeaconVals.labelNumber = []
            return "successful destroy"

        l = locs[1:]
        if (locs[0] == "GET"):
            outfile = "backup2.txt"
            with open(outfile, 'w') as file:
                file.writelines('\t'.join(str(j) for j in i) + '\n' for i in BeaconVals.points)
            outfile2 = "backuplabels2.txt"
            with open(outfile2, 'w') as file:
                file.writelines(str(self.rooms[i]) + '\n' for i in BeaconVals.labelNumber)
            locs = map(int, l)
            if (len(BeaconVals.labelNumber) < self.K):
                ret = "not enough data,"
                ret += str(len(BeaconVals.labelNumber))
                return ret
            K = KNearestNeighbors(self.K, BeaconVals.points, BeaconVals.labelNumber)
            location = K.classifier(locs)
            return self.rooms[location] + ",LOL"
        ID = locs[0]
        intID = int(ID)
        locs = map(int, l)
        BeaconVals.points.append(locs)
        BeaconVals.labelNumber.append(intID)
        cloudserver.db.SaveLocationData(intID, locs)
        return str(len(BeaconVals.labelNumber)) + " LOL"

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

locationTraining = web.application(urls, locals());
