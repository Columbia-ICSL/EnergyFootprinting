import time
from threading import Thread

def myloop(i):
	while True:
		print "i am %d" % i
		time.sleep(5)

t=Thread(target=myloop,args=(1))
t.start()
