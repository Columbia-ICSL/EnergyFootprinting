import DBScrape
import csv
import os

try:
	os.remove('registration_col1.csv')
except OSError:
    pass
    
db=DBScrape.DBScrape()

regList = db.registration_col1()
with open('registration_col1.csv', 'wb') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for person in regList:
		writeArray = []
		writeArray.append(person['control'])
		writeArray.append(person['name'])
		writeArray.append(person['userID'])
		writeArray.append(person['loggedIn'])
		writeArray.append(person['balance'])
		writeArray.append(person['password'])
		writeArray.append(person['email'])
		spamwriter.writerow(writeArray)

