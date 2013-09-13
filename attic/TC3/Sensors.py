#!/usr/bin/env python

class Sensors():
	def __init__(self):
		pass
		
	def decode(self, data):
		mgnt = data[0:2]
		sun_sensor1 = data[2:4]
		sun_sensor2 = data[4:6]
		sun_sensor3 = data[6:8]
		sun_sensor4 = data[8:10]
		sun_sensor5 = data[10:12]
		sun_sensor6 = data[12:14]
		
		return 	"Sensors\n" + \
				"\tMagnetomerter : " + str(mgnt) + "\n" + \
				"\tSun Sensor 1 : " + str(sun_sensor1) + "\n" + \
				"\tSun Sensor 2 : " + str(sun_sensor2) + "\n" + \
				"\tSun Sensor 3 : " + str(sun_sensor3) + "\n" + \
				"\tSun Sensor 4 : " + str(sun_sensor4) + "\n" + \
				"\tSun Sensor 5 : " + str(sun_sensor5) + "\n" + \
				"\tSun Sensor 6 : " + str(sun_sensor6) + "\n"
