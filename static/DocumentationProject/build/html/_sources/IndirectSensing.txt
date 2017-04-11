Indirect Sensing
================

HVAC Sensing
------------
We use a combination of `Modern Devices' Wind Sensor Rev C <https://moderndevice.com/product/wind-sensor/>`_ in addition to the Intel Edison board to monitor air flow.

Before beginning, we must install the mraa package for accessing the analog input pins::

	echo "src mraa-upm http://iotdk.intel.com/repos/1.1/intelgalactic" > /etc/opkg/mraa-upm.conf
	opkg update
	opkg install mraa

We also run jumper wires from (Edison to Wind Sensor):

* 5V to +V
* GND to GND
* A0 to RV
* A1 to TMP

We load the program testProgram.py into /home/root::

	import mraa
	import urllib2
	import json
	
	x = mraa.Aio(1)
	y = mraa.Aio(0)
	
	zeroWindAdjustment = 0.2
	windAD = y.readFloat()* 5.0 * 204.8
	RVWindV = windAD * 0.0048828125
	
	fl = x.readFloat() * 5.0 * 204.8
	temp = 0.005 * fl * fl - 16.862 * fl + 9075.4
	print(temp/100.0)
	
	zeroWind_ADunits = -0.0006*fl*fl + 1.0727*fl + 47.172
	zeroWind_volts = zeroWind_ADunits*0.0048828125 - zeroWindAdjustment
	WindSpeed = 0.0
	if (RVWindV > zeroWind_volts):
	    WindSpeed = pow(((RVWindV - zeroWind_volts)/0.2300), 2.7265)
	
	mph = WindSpeed*1609.34
	m3ph = mph*.17545*2 #ducts are .17545 meters^2, two of them
	
	inputTemp = (55-32)*5/9
	tempDiff = abs(inputTemp - temp/100.0)
	hfr = m3ph*1.2754*1.005*0.27777778
	print(hfr)
	
	url = "http://icsl.ee.columbia.edu:8000/api/EnergyReport/nwcM1_fcu"
	data = {
	    'energy':hfr
	}
	
	req = urllib2.Request(url)
	req.add_header('Content-Type', 'application/json')
	response = urllib2.urlopen(req, json.dumps(data))

This program reads the data from the Aio pin on the Intel Edison, and sends the data via RESTful API to the server.

We also set up a service (autorun.service) to run the program in the background every ten seconds::

	[Unit]
	Description=Wind Speed Sensing
	Wants=network-online.target
	After=network-online.target
	
	[Service]
	ExecStart=/usr/bin/python2.7 /home/root/testProgram.py
	Restart=always
	RestartSec=10s
	Environment=NODE_ENV=production
	
	[Install]
	WantedBy=multi-user.target

We simply call

* systemctl daemon-reload
* systemctl enable autorun.service

And after a restart, the service will begin sending data to the server.
