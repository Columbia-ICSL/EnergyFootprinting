import json
import web
import cloudserver

urls = (
"/","BeaconVals")

class BeaconVals:
    points = [[-90, -90, -90, -90, -90, -90],
              [-89, -89, -89, -89, -89, -89]]
    def nn(self, p):
        min_dist = 1000000;
	    for j in range(len(self.points)):
	        index = -1
                sum_dist = 0
                for k in range(len(p)):
                    ps = self.points[j]
                    sum_dist += (ps[k] - p[k]) * (ps[k] - p[k])
                    if (sum_dist < min_dist):
                        min_dist = sum_dist
                        index = j
        return index

    def POST(self):
        raw_data=web.data()
	    locs = raw_data.split(',')
	    l = locs[1:]
        assert(len(l) == 6)
	    locs = map(int, l)
        return raw_data#self.nn(locs)
	
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
