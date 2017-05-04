import DBScrape
import csv
import os
import argparse
import calendar
import datetime


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", help="how many days back to start scrape", type=int)
parser.add_argument("-e", "--end", help="how many days back to end scrape", type=int)
parser.add_argument("-o", "--offset", help="how many hours to offset scrape", type=int)
args = parser.parse_args()


#set defaults
end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60 #1 day
hours = 0
if (args.start):
	start = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*args.start
if (args.end):
	end = calendar.timegm(datetime.datetime.utcnow().utctimetuple())-24*60*60*args.end
assert(start < end)

if (args.offset):
	start += 60*60*args.offset
	end += 60*60*args.offset

print(datetime.datetime.fromtimestamp(start))
print(datetime.datetime.fromtimestamp(end))


try:
    os.remove('userSnapshots.csv')
except OSError:
    pass

db=DBScrape.DBScrape()

users = db.registration_col1()
shots = db.snapshots_col_users(start, end)

with open('userSnapshots.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	writeArray = []
	writeArray += ["year", "month", "day", "hour", "minute", "second", "HVAC", "Light", "Electric"]
	spamwriter.writerow(writeArray)
	deviceList = ["nwc1007_plug1", "nwc1007_plug2", "nwc1008_plug1", "nwc1008_smartvent1", "nwc1008_light", "nwc1003b_a_plug",
			"nwc1003b_b_plug", "nwc1003b_c_plug", "nwc1003g1_vav", "nwc1003t2_vav", "nwc1003o1_vav", "nwc1008_fcu", "nwcM2_fcu",
			"nwcM3_fcu", "nwcM1_fcu", "nwcM4_fcu", "nwc1003g_a_plug1", "nwc1003g_a_plug2", "nwc1003g_plug1", "nwc1003g_plug2", "nwc1003g_plug3",
			"nwc1003b_light", "nwc1003g_light", "nwc1003gA_vav", "nwc1003gB_vav", "nwc1003gC_vav", "nwc1003A_vav",
			"nwc1003B_vav", "nwc1001L_vav", "nwc10T1_vav", "nwc10F_vav", "nwc8F_vav", "nwc7F_vav", "nwc1000m_a1_plug1",
			"nwc1000m_a1_plug2", "nwc1000m_a2_plug1", "nwc1000m_a2_plug2", "nwc1000m_a3_plug1", "nwc1000m_a3_plug2", "nwc1000m_a4_plug1",
			"nwc1000m_a4_plug2", "nwc1000m_a5_plug1", "nwc1000m_a5_plug2", "nwc1000m_a6_plug1", "nwc1000m_a6_plug2", "nwc1000m_a7_plug1",
			"nwc1000m_a7_plug2", "nwc1000m_a8_plug1", "nwc1000m_a8_plug2", "nwc1000m_a6_plug3", "nwc1000m_a6_plug4", "nwc1000m_a1_plug3",
			"nwc1000m_light", "nwc10hallway_light", "nwc10elevator_light", "nwc8_light", "nwc7_light"]
	writeArray = writeArray + deviceList
	for shot in shots:
		D = shot["timestamp"]
		userList = shot["data"]
		writeArray = []
		#writeArray.append(D.year)
		#writeArray.append(D.month)
		#writeArray.append(D.day)
		#writeArray.append(D.hour)
		#writeArray.append(D.minute)
		#writeArray.append(D.second)	
		A = {"nwc1007_plug1":0, "nwc1007_plug2":0, "nwc1008_plug1":0, "nwc1008_smartvent1":0, "nwc1008_light":0, "nwc1003b_a_plug":0,
			"nwc1003b_b_plug":0, "nwc1003b_c_plug":0, "nwc1003g1_vav":0, "nwc1003t2_vav":0, "nwc1003o1_vav":0, "nwc1008_fcu":0, "nwcM2_fcu":0,
			"nwcM3_fcu":0, "nwcM1_fcu":0, "nwcM4_fcu":0, "nwc1003g_a_plug1":0, "nwc1003g_a_plug2":0, "nwc1003g_plug1":0, "nwc1003g_plug2":0, "nwc1003g_plug3":0,
			"nwc1003b_light":0, "nwc1003g_light":0, "nwc1003gA_vav":0, "nwc1003gB_vav":0, "nwc1003gC_vav":0, "nwc1003A_vav":0,
			"nwc1003B_vav":0, "nwc1001L_vav":0, "nwc10T1_vav":0, "nwc10F_vav":0, "nwc8F_vav":0, "nwc7F_vav":0, "nwc1000m_a1_plug1":0,
			"nwc1000m_a1_plug2":0, "nwc1000m_a2_plug1":0, "nwc1000m_a2_plug2":0, "nwc1000m_a3_plug1":0, "nwc1000m_a3_plug2":0, "nwc1000m_a4_plug1":0,
			"nwc1000m_a4_plug2":0, "nwc1000m_a5_plug1":0, "nwc1000m_a5_plug2":0, "nwc1000m_a6_plug1":0, "nwc1000m_a6_plug2":0, "nwc1000m_a7_plug1":0,
			"nwc1000m_a7_plug2":0, "nwc1000m_a8_plug1":0, "nwc1000m_a8_plug2":0, "nwc1000m_a6_plug3":0, "nwc1000m_a6_plug4":0, "nwc1000m_a1_plug3":0,
			"nwc1000m_light":0, "nwc10hallway_light":0, "nwc10elevator_light":0, "nwc8_light":0, "nwc7_light":0}
		for userID in userList:
			#writeArray.append(userList[userID]["location"])
			consumptions = userList[userID]["consumptions"]
			for device in consumptions:
				if device["id"] in A:
					A[device["id"]] += 1
				else:
					A[device["id"]] = 1
		for device in deviceList:
			writeArray.append(A[device])
		spamwriter.writerow(writeArray)
#	for person in users:
#		personID = person["userID"]
#		writeArray.append(personID)
#	spamwriter.writerow(writeArray)
#
#	for shot in shots:
#		D = shot["timestamp"]
#		userList = shot["data"]
#		writeArray = []
#		writeArray.append(D.year)
#		writeArray.append(D.month)
#		writeArray.append(D.day)
#		writeArray.append(D.hour)
#		writeArray.append(D.minute)
#		writeArray.append(D.second)
#		if 
#		for person in users:
#			userFound = False
#			personID = person["userID"]
#			if personID in userList:
#				consumptions = userList[personID]["value"]
#				for 
#				writeArray.append(userList[personID]["value"])
#				userFound = True
#				continue
#			if (not userFound):
#				writeArray.append(0)

#		spamwriter.writerow(writeArray)

