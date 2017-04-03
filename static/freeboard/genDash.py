import json
from collections import OrderedDict as ODict
import urllib2

###### Widget Associations ##########
widgets = [["gauge_widget", "Energy", 0, "Watts"],
	["text_widget", "Location", 1, ""], 
	["text_widget", "Last Seen", 2, "Seconds ago"]]


data = ODict()

data["version"] = 1
data["allow_edit"]=False
data["plugins"]=["/view/board/tutorial.min.js", "/plugins/all"]

userNames = urllib2.urlopen("http://icsl.ee.columbia.edu:8000/api/appSupport/userNames/").read()
#print userNames

userNames = json.loads(userNames)
userNames = userNames["names"]
#print userNames

data["panes"] = []

for user in userNames:
    temp = ODict()
    temp["title"] = user
    temp["width"] = 1
    temp["row"] = {"3":1}
    temp["col"] = {"3":3}
    temp["col_width"] = 1
    temp["widgets"] = []
    for widget in widgets:
    	temp["widgets"].append({
        "type":widget[0],
        "settings": {
            "title": widget[1],
            "size": "regular",
            "value": "datasources[\"ices\"][\""+user+"\"]["+str(widget[2])+ "]",
            "animate": True,
            "units": widget[3],
            "min_value":0,
            "max_value":1500
            }
        }
    )
    data["panes"].extend([temp])
    #print user
    #print json.dumps(temp, indent=4)

data["datasources"] = [{
    "name":"ices",
    "type":"JSON",
    "settings": {
        "url": "http://icsl.ee.columbia.edu:8000/api/appSupport/localization/",
        "use_thingproxy": "false",
        "refresh": 5,
        "method": "GET"
        }
    }]
data["columns"] = 3
print json.dumps(data, indent=4)
