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
    K = 3
    KNN = KNearestNeighbors(3, points, labelNumber)
    rooms = ["nwc4", "nwc7", "nwc8", "nwc10", "nwc10m", "nwc1000m_a1", "nwc1000m_a2", "nwc1000m_a3", "nwc1000m_a4", "nwc1000m_a5", "nwc1000m_a6", "nwc1000m_a7", "nwc1000m_a8", "nwc1003b", "nwc1003g","nwc1006", "nwc1007", "nwc1008", "nwc1009", "nwc1010", "nwc1003b_t", "nwc1003b_a", "nwc1003b_b", "nwc1003b_c"]
    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')
        #if (locs[0] == "SAVE"):
        #    print("saved")
        #    outfile = "backup.txt"
        #    with open(outfile, 'w') as file:
        #        file.writelines('\t'.join(str(j) for j in i) + '\n' for i in cloudserver.trainingData)
        #    outfile2 = "backuplabels.txt"
        #    with open(outfile2, 'w') as file:
        #        file.writelines('\t'.join(str(j) for j in i) + '\n' for i in cloudserver.trainingLabels)
        #    return "written"
        if (locs[0] == "DES"):
            cloudserver.trainingData = []
            cloudserver.trainingLabels = []
            cloudserver.db.DestroyLocationData()
            return "successful destroy"
        l = locs[1:]

        if (locs[0] == "GET"):
            outfile = "backup.txt"
            with open(outfile, 'w') as file:
                file.writelines('\t'.join(str(j) for j in i) + '\n' for i in cloudserver.trainingData)
            outfile2 = "backuplabels.txt"
            with open(outfile2, 'w') as file:
                file.writelines(str(self.rooms[i]) + '\n' for i in cloudserver.trainingLabels)
            locs = map(int, l)
            if (len(cloudserver.trainingLabels) <= self.K):
                return "not enough data, LOL"
            K = KNearestNeighbors(self.K, cloudserver.trainingData, cloudserver.trainingLabels)
            location = K.classifier(locs)
            return self.rooms[location] + ",LOL"
        ID = locs[0]
        intID = int(ID)
        locs = map(int, l)
        cloudserver.trainingData.append(locs)
        cloudserver.trainingLabels.append(intID)
        cloudserver.db.SaveLocationData(intID, locs)
        return "success"

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
        return result

locationTraining = web.application(urls, locals());
