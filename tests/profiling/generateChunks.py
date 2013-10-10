#! /usr/bin/env python

import os
from utils import splitImageIntoChunks

width = 500
height = 500
directory = "chunks/"
imagesdir = "images/"

images = os.listdir(imagesdir)
for image in images:
    splitImageIntoChunks(imagesdir + image, directory, width, height)
