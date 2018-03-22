from separateFootprint import getFootprints
import plotGraphs
import sys

from spaceNames import S
#contains the spaces
print "This is the name of the script: ", sys.argv[0]
print "Number of arguments: ", len(sys.argv)
if len(sys.argv) != 7:
	print "Supply arguments to this script. Example: python separateFootprint.py {beginYear} {beginMonth} {beginDay} {endYear} {endMonth} {endDay}"
	assert(len(sys.argv) == 7)


parameters = sys.argv[1:]
for i in range(len(parameters)):
	parameters[i] = int(parameters[i])

GF = getFootprints(S, True)
GF.getSnapshots(parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5])
GF.saveTimeSeries()
