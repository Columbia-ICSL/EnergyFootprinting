from separateFootprint import getParameters

import sys
print "This is the name of the script: ", sys.argv[0]
print "Number of arguments: ", len(sys.argv)
if len(sys.argv) != 8:
	print "Supply arguments to this script. Example: python separateFootprint.py {parameter name} {beginYear} {beginMonth} {beginDay} {endYear} {endMonth} {endDay}"
	assert(len(sys.argv) == 8)

parameters = sys.argv[2:]
for i in range(len(parameters)):
	parameters[i] = int(parameters[i])

p = sys.argv[1]

GP = getParameters()
GP.getParameter(p, parameters[0], parameters[1], parameters[2], parameters[3], parameters[4], parameters[5])