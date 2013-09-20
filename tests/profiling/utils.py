#! /usr/bin/env python

import os
import numpy
import Image
import ImageFilter

def read(filename):
	image = open(filename, "r")
	data = image.read()
	image.close()
	return data

def write(filename, data):
    image = open(filename, "w")
    image.write(data)
    image.close()

def process(filename):
    # basic find edges
    image = Image.open(filename)
    edges = image.filter(ImageFilter.FIND_EDGES)
    edges.save("results/e" + os.path.split(filename)[1])
    # image -> fft -> ifft -> image
    image = Image.open(filename)
    bands = image.split()
    for i, band in enumerate(bands):
        numpyArray = numpy.asarray(band)
        fftArray = numpy.fft.rfft2(numpyArray)
        ifftArray = numpy.fft.irfft2(fftArray)
        result = Image.fromarray(ifftArray.astype(numpy.uint8))
        result.save("results/f" + str(i) + os.path.split(filename)[1])
