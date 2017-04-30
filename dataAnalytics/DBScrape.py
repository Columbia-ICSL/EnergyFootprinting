import pymongo

db=DBScrape()

class DBScrape():
	def __init__(self):
		self.dbc=pymongo.MongoClient()

		self.registration_col1=self.dbc.db.registration_col1
		print(list(self.registration_col1.find()))
		return