import urllib2
import json
import os
import csv
import datetime
import time


apiURL = 'http://api.wunderground.com/api/41e9482d39e03f1e/history_'
#year = '2017'
#month = '04'
#day = '01'
endURL = '/q/NY/New_York.json'

#f = urllib2.urlopen(apiURL + year + month + day + endURL)
#json_string = f.read()
#parsed_json = json.loads(json_string)
#observations = parsed_json["history"]["observations"]
#for time in observations:
#	hour = time["date"]["hour"]
#	minute = time["date"]["min"]
#	temperature = time["tempi"]
#	print((hour, minute, temperature))

#f.close()

#beginDate = datetime.datetime(2017, 9, 14, 12, 0, 0)

def getTemp2(beginDay, endDay, month, year):
	temperatures = []
	timestamps = []
	try:
		os.remove('weatherData.csv')
	except OSError:
		pass
	with open('weatherData.csv', 'wb') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=' ',
								quotechar='|', quoting=csv.QUOTE_MINIMAL)


		for i in range(beginDay, endDay):

			if (month > 9):
				monthURL = str(month)
			else:
				monthURL = "0" + str(month)
			if (i > 9):
				day = str(i)
			else:
				day = "0" + str(i)
			URL = apiURL + str(year) + monthURL + day + endURL

			f = urllib2.urlopen(apiURL + str(year) + monthURL + day + endURL)
			json_string = f.read()
			parsed_json = json.loads(json_string)
			observations = parsed_json["history"]["observations"]
			for timei in observations:
				yeari = int(timei["date"]["year"])
				monthi = int(timei["date"]["mon"])
				dayi = int(timei["date"]["mday"])
				houri = int(timei["date"]["hour"])
				minutei = int(timei["date"]["min"])
				temperature = float(timei["tempi"])
				D = datetime.datetime(yeari, monthi, dayi, houri, minutei, 0)
				timestamp = time.strftime("%d-%b-%Y %H:%M:%S", D.utctimetuple())
				temperatures.append(temperature)
				timestamps.append(timestamp)


				#print((hour, minute, temperature))
			f.close()
		spamwriter.writerow(temperatures)
	try:
		os.remove('weatherDataTimestamps.csv')
	except OSError:
		pass
	with open('weatherDataTimestamps.csv', 'wb') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=',',
								quotechar='|', quoting=csv.QUOTE_MINIMAL)
		spamwriter.writerow(timestamps)
	print(temperatures)


getTemp2(14, 22, 9, 2017)








def getTemp1():
	temperatures = [0] * 96 * 30
	year = '2017'
	month = '04'
	day = '01'
	try:
		os.remove('weatherData.csv')
	except OSError:
		pass
	with open('weatherData.csv', 'wb') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=' ',
								quotechar='|', quoting=csv.QUOTE_MINIMAL)

		tempIndex = 0
		for i in range(1, 31):
			if (i > 9):
				day = str(i)
			else:
				day = "0" + str(i)
			f = urllib2.urlopen(apiURL + year + month + day + endURL)
			json_string = f.read()
			parsed_json = json.loads(json_string)
			observations = parsed_json["history"]["observations"]
			for time in observations:
				if tempIndex >= 96*30:
					continue
				yeari = int(time["date"]["year"])
				monthi = int(time["date"]["mon"])
				dayi = int(time["date"]["mday"])
				houri = int(time["date"]["hour"])
				minutei = int(time["date"]["min"])
				temperature = float(time["tempi"])
				
				minFromStart = (dayi-1)*1440 + houri*60 + minutei
				while tempIndex*15 < minFromStart:
					temperatures[tempIndex] = temperature
					tempIndex += 1

				#print((hour, minute, temperature))
			f.close()
		spamwriter.writerow(temperatures)
	print(temperatures)
