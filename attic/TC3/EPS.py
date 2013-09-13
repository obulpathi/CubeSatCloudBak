#!/usr/bin/env python

from Common import *

class Battery():	
	def __init__(self):
		pass

	def decode(self, data):
		volt = data[0:2]
		curr = data[2:4]
		temp = data[4:6]

		return 	"\tBattery\n" + \
				"\t\tVoltage : " + str(volt) + "\n" + \
				"\t\tCurrent : " + str(curr) + "\n" + \
				"\t\tTemperature : " + str(temp) + "\n"

class Cell():
	def __init__(self):
		pass
	
	def decode(self, data):
		return "\tCell\n"


class SolarCell():
	SCID = 0
	
	# initialize
	def __init__(self, scid):
		self.SCID = scid
		
	# define access functions
	def get_temp(self):
		return temp
	
	def get_cur(self):
		return cur
	
	def get_volt(self):
		return volt
	
	def decode(self, data):
		volt = data[0:2]
		curr = data[2:4]
		temp = data[4:6]
		
		return 	"\tSolar cell " + str(self.SCID) + "\n" + \
				"\t\tVoltage : " + str(volt) + "\n" + \
				"\t\tCurrent : " + str(curr) + "\n" + \
				"\t\tTemperature : " + str(temp) + "\n"


class EPS():
	batt = Battery()
	sc1 = SolarCell(1)
	sc2 = SolarCell(2)
	sc3 = SolarCell(3)
	sc4 = SolarCell(4)

	def __init__(self):
		pass
	
	def decode(self, data):
		return "EPS\n" + self.batt.decode(data) + self.sc1.decode(data) + self.sc2.decode(data) + self.sc3.decode(data) + self.sc4.decode(data)
