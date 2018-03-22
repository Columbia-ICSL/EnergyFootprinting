import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.switch_backend('tkagg')
class footprintPlots:
	def __init__(self):
		print "Hello World!"

	def plotFootprints(self, footprints, timestamps):
		myFmt = mdates.DateFormatter('%H:%M')
		print "Showing plot..."
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
		plt.show(1)