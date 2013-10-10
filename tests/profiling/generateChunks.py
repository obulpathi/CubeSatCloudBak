#! /usr/bin/env python

import os
import Image
from utils import splitImageIntoChunks

# configuration
width = 500
height = 500
directory = "chunks/"
imagesdir = "images/"

# create chunks
images = os.listdir(imagesdir)
for image in images:
    splitImageIntoChunks(imagesdir + image, directory, width, height)

# cleanup small chunks
chunks = os.listdir(directory)
for chunk in chunks:
    filename = "chunks/" + chunk
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    if (width < 500) or (height < 500):
        os.remove(filename)
