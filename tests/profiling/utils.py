#! /usr/bin/env python

import os
import math
import numpy
import Image
import ImageFilter
from uuid import uuid4
from collections import namedtuple

WIDTH = 500
HEIGHT = 500
Box = namedtuple('Box', 'left top right bottom')
class Chunk(object):
    def __init__(self, uuid, name, size, box):
        self.uuid = uuid
        self.name = name
        self.size = size
        self.box = box
        self.status = "UNASSIGNED"
        self.worker = None
    def __repr__(self):
        return "Name: " + str(self.name) + ", Size: " + str(self.size) + \
               ", Box: " + str(self.box) + ", Status: " + str(self.status) + ", Worker: " + str(self.worker)
               
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

# split the remote sensing data into chunks
def splitImageIntoChunks(filename, directory):
    metadata = {}
    chunks = {}
    # check if the file exists
    if not os.path.isfile(filename):
        print("Error: no such file: %s exists" % filename)
        exit(1)
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    prefix = os.path.basename(filename).split(".")[0] + "/"
    # create data subdirectory for this file
    try:
        os.mkdir(directory + prefix)
    except:
        pass
    count = 0 # chunk counter
    for y in range(0, int(math.ceil(float(height)/HEIGHT))):
        for x in range(0, int(math.ceil(float(width)/WIDTH))):
            left = x * WIDTH
            top = y * HEIGHT
            right = min((x+1) * WIDTH, width)
            bottom = min((y+1) * HEIGHT, height)
            # box = (left, top, right, bottom)
            data = image.crop((left, top, right, bottom))
            chunkname = directory + prefix + str(count) + ".jpg"
            data.save(chunkname)
            size = os.stat(chunkname).st_size
            box = Box(left, top, right, bottom)
            chunk = Chunk(uuid4(), prefix + os.path.split(chunkname)[1], size, box)
            chunks[chunk.uuid] = chunk
            count = count + 1
    metadata["filename"] = filename
    metadata["directory"] = directory
    metadata["width"] = width
    metadata["height"] = height
    metadata["size"] = "SIZE"
    metadata["chunkMap"] = {}
    return (chunks, metadata)
