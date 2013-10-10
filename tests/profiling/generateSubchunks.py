#! /usr/bin/env python

import os
import Image
from utils import splitImageIntoChunks

SIZE = 100
directory = "subchunks/"
chunksdir = "misc/"

chunks = os.listdir(chunksdir)
for chunk in chunks:
    filename = "misc/" + chunk
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    for x in range(5):
        left = 0
        top = 0
        right = SIZE * (x+1)
        bottom = SIZE * (x+1)
        data = image.crop((left, top, right, bottom))
        chunkname = directory + str(x+1) + ".jpg"
        data.save(chunkname)
