#!/usr/bin/env python

class COMMS():
	def __init__(self):
		pass
	
	def decode(self, data):
		tx_curr = data[0:2]
		rx_curr = data[2:4]
		msp_temp = data[4:6]
		
		return 	"COMMS\n" + \
				"\tTransmitter Current : " + str(tx_curr) + "\n" + \
				"\tReceiver Current : " + str(rx_curr) + "\n" + \
				"\tMSP430 Temperature : " + str(msp_temp) + "\n"
