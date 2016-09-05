
import web

urls = (
  "", "reblog",
  "/task/(.?)","signing",
  "/blog/(.*)","blog",
  "/app/(.+)","append"
)

class reblog:
  def GET(self): raise web.seeother('/')

class blog:
  def GET(self, path):
    return "blog " + path
class append:
  def GET(self,path):
      print(path)
      return "append "+" web input is "+str(web.input())
class signing:
  def GET(self,query):
      pass
      return query+" "+str(web.input())
app_blog = web.application(urls, locals())
