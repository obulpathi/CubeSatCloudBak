#!/usr/bin/env python

import sys

from Header import *
from ADS import *
from EPS import *
from COMMS import *
from Sensors import *

class Packet():
	# define state
	header = Header()
	ads = ADS()
	comms = COMMS()
	eps = EPS()	
	imu = IMU()
	sensors = Sensors()
	
	# define functions
	def __init__(self):
		pass
	
	def decode(self, data):
		# validate header
		if not self.header.check(data):
			print "Packet validation failed!"
			print "Aborting packet decoding"
			sys.exit(1)			
			
		msg = ""
		# decode ads data
		msg = msg + self.ads.decode(data[0:20])
		# decode comms data
		msg = msg + self.comms.decode(data[10:30])
		# decode eps data
		msg = msg + self.eps.decode(data[20:40])
		# decode sensors data
		msg = msg + self.sensors.decode(data[30:50])		

		return msg

def main():
	packet = Packet()

	# get data
	data = "24421237812647823C7456BFR87F7345B38F5237O4FB375FQ2FDHFJKSDFHASKFHJKASHFLAK743Y7IFVHATB7SFG34L5F7578FB465FB766666348OBCF6348FG637TBGO58344448"

	# decode the data
	msg = packet.decode(data)
	
	# return the message
	print msg

if __name__ == "__main__":
	main()
