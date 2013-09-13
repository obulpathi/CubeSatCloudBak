#!/us/bin/env python

class Header():
	SSID = "2442"
	
	def __init__(self):
		pass
	
	def check(self, packet):
		if packet[0:4] == self.SSID :
			return True
		else :
			return False
