#! /usr/bin/env python

def read(filename):
	image = open(filename, "r")
	data = image.read()
	image.close()
	return data

def write(filename, data):
    image = open(filename, "w")
    image.write(data)
    image.close()

def readWrite(source, sink):
    data = read(source)
    write(sink, data)
