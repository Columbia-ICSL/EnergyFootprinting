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
footprints = GF.getSnapshots(parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5])
timestamps = GF.getTimestamps()
GF.saveTimeSeries()

myFmt = mdates.DateFormatter('%H:%M')

plt.figure(1)
handlerArray = []
for room in footprints:
	a, = plt.plot(timestamps, footprints[room], label=room)
	handlerArray.append(a)
plt.gcf().autofmt_xdate()
plt.gca().xaxis.set_major_formatter(myFmt)
plt.xlabel('Time of Day')
plt.ylabel('Energy Consumption')
plt.legend(handles=handlerArray)
plt.show()