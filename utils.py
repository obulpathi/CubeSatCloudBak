import os
import math
import pickle
from PIL import Image
from uuid import uuid4

from cloud.common import *

# save the metadata into file
def saveMetadata(metadata):
    metadatadir = "/home/obulpathi/phd/cloud/data/master/metadata/"
    filename = metadatadir + "image.jpg" # get the base name of the file here
    metafile = open(filename, "w")
    metastring = pickle.dumps(metadata)
    metafile.write(metastring)
    metafile.close()

# change the status of the chunks, after reading metadata        
def loadMetadata(filename):
    #log.msg("Loading metadata for the file: %s" % filename)
    metadatadir = "/home/obulpathi/phd/cloud/data/master/metadata/"
    filename = metadatadir + filename
    metafile = open(filename)
    metastring = metafile.read()
    metafile.close()
    metadata = pickle.loads(metastring)
    return metadata
    
# split the remote sensing data into chunks
#def splitImageIntoChunks(filename, directory):
def splitImageIntoChunks(filename):
    metadata = {}
    chunks = {}
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    prefix = filename.split(".")[0] + "/"
    # create data subdirectory for this file
    directory = "/home/obulpathi/phd/cloud/data/master/"
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

# stich chunks into image
def stichChunksIntoImage(directory, filename, metadata):
    print("##############################################################################################")
    print("##############################################################################################")
    print("##############################################################################################")
    width = metadata["width"]
    height = metadata["height"]

    # creates a new empty image, RGB mode, and size width by height
    result = Image.new('RGB', (width, height))

    chunkMap = metadata["chunkMap"]
    print(chunkMap)
    for chunks in chunkMap.itervalues():
        for chunk in chunks:
            # fetch the chunk
            data = Image.open(directory + chunk.name)
            print(chunk.box)
            result.paste(data, (chunk.box.left, chunk.box.top))
    result.save(filename)
    return
