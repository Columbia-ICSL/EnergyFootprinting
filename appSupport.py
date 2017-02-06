import web
import cloudserver

urls = ("/", "appSupport")

class appSupport:
	def POST(self):
		return "hello world"

appURL = web.application(urls, locals());
