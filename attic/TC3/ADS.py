#!/usr/bin/env python

class MagnetCoil():
	def __init__(self):
		pass
	
	def decode(self, data):
		on_time = data[0:2]
		off_time = data[2:4]
		
		return 	"\tMagnet Coil\n" + \
				"\t\tOn time : " + str(on_time) + "\n" + \
				"\t\tOfftime : " + str(off_time) + "\n"

class IMU():
	def __init__(self):
		pass
	
	def decode(self, data):
		angular_rate = data[0:2]
		temp1 = data[2:4]
		temp2 = data[4:6]
		temp3 = data[6:8]
		temp4 = data[8:10]
		flywheel_speed = data[10:12]
		gimbal_rate = data[12:14]
		gimbal_angles = data[14:16]
		
		return 	"\tIMU\n" + \
				"\t\tAngular rate : " + str(angular_rate) + "\n" + \
				"\t\tTemperature 1 : " + str(temp1) + "\n" + \
				"\t\tTemperature 2 : " + str(temp2) + "\n" + \
				"\t\tTemperature 3 : " + str(temp3) + "\n" + \
				"\t\tTemperature 4 : " + str(temp4) + "\n" + \
				"\t\tFlywheel Speed : " + str(flywheel_speed) + "\n" + \
				"\t\tGimbal Rate : " + str(gimbal_rate) + "\n" + \
				"\t\tGimbal Angles : " + str(gimbal_angles) + "\n"

class ADS():
	coil = MagnetCoil()
	imu = IMU()
	
	def __init__(self):
		pass
	
	def decode(self, data):
		return "ADS\n" + self.coil.decode(data) + self.imu.decode(data)
