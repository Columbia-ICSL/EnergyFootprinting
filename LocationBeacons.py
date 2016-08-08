import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors

urls = (
"/","BeaconVals")

class BeaconVals:
    points = [[-90, -90, -90, -90, -90, -90],
              [-89, -89, -89, -89, -89, -89]]
    labels = ["Peter's Desk", "Danny's Desk", "Steven's Desk", "Rishi's Desk", "Daniel's Desk", "ICSL Lab Space", "Tehrani Lab Space", "4th Lab Space", "Bio Lab Space", "Professor's Office", "Hallway", "10M"]
    KNN = KNearestNeighbors(3, points, labels)
    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')
        l = locs[1:]
#        assert(len(l) == 11)
        locs = map(int, l)
        cloudserver.db.SaveLocationData(0, raw_data)
        location = self.KNN.classifier(locs)
        return location[0]#self.nn(locs)
	
	#total = 0
	#for i in range(len(locs)):
	#	if (i == 0):
	#		continue
	#	total += int(locs[i])
	#	
	#cloudserver.db.SaveLocationData(0, raw_data)
        #return str(total)

    def GET(self):
        result = cloudserver.db.QueryLocationData(0)
#	return result
        return result

Beacons = web.application(urls, locals());
