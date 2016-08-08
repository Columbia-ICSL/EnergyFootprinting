import json
import web
import cloudserver
from KNNalgo import KNearestNeighbors

urls = (
"/","BeaconVals")

class BeaconVals:
    points = [[-96,-100,-100,-100,-88,-90,-64,-84,-100,-100,-100],
              [-100,-94,-100,-93,-99,-92,-67,-85,-100,-100,-100],
              [-93,-100,-91,-100,-88,-91,-63,-81,-100,-100,-100],
              [-91,-95,-94,-94,-88,-100,-76,-80,-100,-100,-100], 
              [-98,-93,-100,-94,-87,-100,-62,-81,-100,-100,-100],
              [-100,-100,-100,-100,-92,-95,-66,-83,-100,-100,-100],
              [-100,-100,-100,-100,-91,-84,-59,-89,-100,-100,-100],
              [-100,-100,-100,-100,-100,-87,-62,-83,-100,-100,-100],
              [-100,-100,-100,-100,-92,-88,-52,-91,-100,-100,-100],
              [-100,-93,-100,-97,-92,-93,-62,-87,-100,-100,-100],
              [-92,-100,-100,-100,-88,-85,-55,-91,-100,-100,-100],
              [-100,-100,-100,-100,-94,-86,-55,-90,-100,-100,-100],
              [-98,-100,-94,-93,-87,-96,-67,-90,-100,-100,-100],
              [-100,-100,-100,-94,-81,-97,-63,-94,-100,-100,-100],
              [-92,-95,-95,-91,-89,-98,-75,-82,-100,-100,-100],
              [-96,-92,-95,-97,-83,-94,-58,-92,-100,-100,-100],
              [-94,-89,-88,-94,-80,-93,-65,-92,-100,-100,-100],
              [-89,-76,-90,-91,-100,-93,-73,-100,-100,-100,-100],
              [-88,-85,-88,-85,-95,-88,-68,-97,-100,-100,-100],
              [-89,-77,-88,-85,-94,-97,-80,-100,-100,-100,-100],
              [-87,-85,-85,-90,-93,-94,-64,-100,-100,-100,-100],
              [-90,-92,-83,-92,-100,-93,-70,-100,-100,-100,-100],
              [-80,-85,-87,-96,-93,-100,-70,-100,-100,-100,-100],
              [-69,-85,-90,-90,-99,-96,-71,-91,-100,-100,-100],
              [-88,-95,-87,-87,-95,-90,-68,-93,-100,-100,-100]
              ]
    labels = ["Peter's Desk", "Danny's Desk", "Steven's Desk", "Rishi's Desk", "Daniel's Desk", "ICSL Lab Space", "Tehrani Lab Space", "4th Lab Space", "Bio Lab Space", "Professor's Office", "Hallway", "10M"]
    labelNumber = [6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 5, 5, 5, 5, 5, 1, 1, 1, 1, 0, 0, 0, 0]
    KNN = KNearestNeighbors(3, points, labelNumber)
    def POST(self):
        raw_data=web.data()
        locs = raw_data.split(',')
        l = locs[1:]
#        assert(len(l) == 11)
        locs = map(int, l)
        location = self.KNN.classifier(locs)
        cloudserver.db.SaveLocationData(0, self.labels[location[0]])
        return self.labels[location[0]]#self.nn(locs)
	
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
