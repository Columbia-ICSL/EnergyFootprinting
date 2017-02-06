import web
import cloudserver

urls = ("/", "appSupport")

class appSupport:
	def GET(self):
		return "hello world"

appSPT = web.application(urls, locals());
