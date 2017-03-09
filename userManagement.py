import web
import cloudserver
urls = ("/","userManagement",
	"/newUser/", "newUserManagement",
	"/checkUser/", "checkLogin",
	"/login/", "login",
	"/logout/", "logout")

class userManagement:
	def POST(self):
		raw_data=web.data()
		userData=raw_data.split(',')
		if (len(userData) == 0):
			return "no username provided"
		length = len(userData)
		deviceID = userData[0]
		if (len(userData) == 1):
			if (not cloudserver.db.deviceIDCheckAvailability(deviceID)):
				return "0" #already registered
			else:
				return "1" #need to register
		if (len(userData) == 2):
			if (not cloudserver.db.deviceIDCheckAvailability(deviceID)): #not available
				return "device already registered"
			if (not cloudserver.db.screenNameCheckAvailability(userData[1])): #not available
				return "screen name taken"
			cloudserver.db.screenNameRegister(userData[1], deviceID, True)
			return "0"
		if (len(userData) == 3):
			cloudserver.db.userIDRemoveAll(deviceID)
			return "0"
		if (len(userData) == 4): # device ID, username, nothing, nothing
			username = userData[1]
			if (cloudserver.db.updateName(deviceID, username)):
				return "0" #successfully changed device ID
			else:
				return "1" #screen name not found
		return "too many parameters"

class newUserManagement:
	def POST(self):
		raw_data=web.data()
		userData=raw_data.split(',')
		if (len(userData) != 4):
			return "1"
		deviceID = userData[0]
		name = userData[1]
		email = userData[2]
		password = userData[3]
		if (cloudserver.db.fullRegistration(deviceID, name, email, password))
			return "0"
		else:
			return "1"

class checkLogin:
	def POST(self):
		raw_data=web.data()
		return cloudserver.db.checkLoginFlow(raw_data)

class login:
	def POST(self):
		raw_data=web.data()
		userData=raw_data.split(',')
		if (len(userData) != 3):
			return "1"
		deviceID = userData[0]
		email = userData[1]
		password = userData[2]
		return cloudserver.db.login(deviceID, email, password)

class logout:
	def POST(self):
		raw_data=web.data()
		return cloudserver.db.logout(raw_data)

	def GET(self):
		user_data = web.input(id=None)
		if user_data.id == None:
			return "Error: please provide valid user ID."
		if (cloudserver.db.getControl(user_data.id) == True):
			return "true"
		else:
			return "false"
		return "true"


userMGM = web.application(urls, locals());

