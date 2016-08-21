import requests

def SendEmail(title, body):
	# TODO: verify sending API
    return requests.post(
        "https://api.mailgun.net/v3/icsl.ee.columbia.edu/messages",
        auth=("api", "key-e9e526b55efd83ffe1c6a0b2200a5ea8"),
        data={"from": "Mailgun Sandbox <postmaster@icsl.ee.columbia.edu>",
              "to": "Xiaoqi <chenxiaoqino+mailgun@gmail.com>, Rishi <rc3022@columbia.edu>,",
              "subject": title,
              "text": body})
