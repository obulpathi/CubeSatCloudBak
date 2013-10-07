import os
import math
import pickle
from PIL import Image
from uuid import uuid4

from cloud.common import *

# save the metadata into file
def saveMetadata(metadata, directory):
    # reconstruct the whole file path
    filename = directory + metadata["filename"].split(".")[0]
    print("Saving metadata for the file: %s" % filename)
    metafile = open(filename, "w")
    metastring = pickle.dumps(metadata)
    metafile.write(metastring)
    metafile.close()

# load the metadata from the given file
# change the status of the chunks, after reading metadata        
def loadMetadata(filename):
    print("Loading metadata for the file: %s" % filename)
    # check if the file exists
    if not os.path.isfile(filename):
        print("Error: no such file: %s exists" % filename)
        exit(1)
    metafile = open(filename)
    metastring = metafile.read()
    metafile.close()
    metadata = pickle.loads(metastring)
    return metadata
    
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
    prefix = filename.split(".")[0] + "/"
    # create data subdirectory for this file
    os.mkdir(directory + prefix)
    count = 0 # chunk counter
    for y in range(0, int(math.ceil(float(height)/chunk_y))):
        for x in range(0, int(math.ceil(float(width)/chunk_x))):
            left = x * chunk_x
            top = y * chunk_y
            right = min((x+1) * chunk_x, width)
            bottom = min((y+1) * chunk_y, height)
            # box = (left, top, right, bottom)
            data = image.crop((left, top, right, bottom))
            chunkname = directory + prefix + str(count) + ".jpg"
            data.save(chunkname)
            size = os.stat(chunkname).st_size
            box = Box(left, top, right, bottom)
            chunk = Chunk(str(uuid4()), prefix + os.path.split(chunkname)[1], size, box)
            chunks[chunk.uuid] = chunk
            count = count + 1
    metadata["filename"] = filename
    metadata["directory"] = directory
    metadata["width"] = width
    metadata["height"] = height
    metadata["size"] = "SIZE"
    metadata["chunkMap"] = {}
    return (chunks, metadata)

# stich chunks into image
def stichChunksIntoImage(directory, filename, metadata):
    width = metadata["width"]
    height = metadata["height"]

    # creates a new empty image, RGB mode, and size width by height
    result = Image.new('RGB', (width, height))

    chunkMap = metadata["chunkMap"]
    print(chunkMap)
    for chunks in chunkMap.itervalues():
        for chunk in chunks:
            chunkname = directory + chunk.name
            # check if the chunk exists
            if not os.path.isfile(chunkname):
                print("Error: no such chunk: %s exists" % chunkname)
                exit(1)
            # fetch the chunk
            data = Image.open(chunkname)
            result.paste(data, (chunk.box.left, chunk.box.top))
    result.save(filename)
    return

def banner(msg):
    print("#############################################################")
    print(msg)
    print("#############################################################")
    return
    
"""
# print a banner
def banner(text, ch='=', length=78):
    if text is None:
        print ch * length
    elif len(text) + 2 + len(ch)*2 > length:
        # Not enough space
        print text
    else:
        remain = length - (len(text) + 2)
        prefix_len = remain / 2
        suffix_len = remain - prefix_len
        if len(ch) == 1:
            prefix = ch * prefix_len
            suffix = ch * suffix_len
        else:
            prefix = ch * (prefix_len/len(ch)) + ch[:prefix_len%len(ch)]
            suffix = ch * (suffix_len/len(ch)) + ch[:suffix_len%len(ch)]
        print prefix + ' ' + text + ' ' + suffix
"""
