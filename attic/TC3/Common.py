#!/usr/bin/env python

class Current():
	# define state
	curr = 0.0

	def __init__(self):
		pass

	# define access functions
	def get_curr(self):
		return self.curr;

	def set_curr(self):
		self.curr = curr;
	
	def decode(self, data):
		print "decode current"


class Temperature():
	# define state
	temp = 0.0

	def __init__(self):
		pass

	# define access functions
	def get_temp(self):
		return self.curr;

	def set_temp(self):
		self.curr = curr;
		
	def decode(self, data):
		print "decode temperature"
		

class Voltage():
	# define state
	volt = 0.0

	def __init__(self):
		pass

	# define access functions
	def get_volt(self):
		return self.volt;

	def set_volt(self):
		self.volt = volt;
	
	def decode(self, data):
		print "decode voltage"
