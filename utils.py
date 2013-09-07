import os
import math
import pickle
from PIL import Image
from uuid import uuid4

from cloud.common import *

#def saveMetadata(metadata, filename):
def saveMetadata(metadata):
    filename = "/home/obulpathi/phd/cloud/data/master/metadata/image.jpg"
    metafile = open(filename, "w")
    metastring = pickle.dumps(metadata)
    metafile.write(metastring)
    metafile.close()

# change the status of the chunks, after reading metadata        
def loadMetadata(filename):
    #log.msg("Loading metadata for the file: %s" % filename)
    filename = "/home/obulpathi/phd/cloud/data/master/metadata/" + filename
    metafile = open(filename)
    metastring = metafile.read()
    metafile.close()
    metadata = pickle.loads(metastring)
    return metadata
    
# split the remote sensing data into chunks
#def splitImageIntoChunks(filename, directory):
def splitImageIntoChunks(filename):
    chunks = {}
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    # create data subdirectory for this file
    directory = "/home/obulpathi/phd/cloud/data/master/" + filename.split(".")[0]
    os.mkdir(directory)
    count = 0 # chunk counter
    for y in range(0, int(math.ceil(float(height)/chunk_y))):
        for x in range(0, int(math.ceil(float(width)/chunk_x))):
            left = x * chunk_x
            top = y * chunk_y
            right = min((x+1) * chunk_x, width)
            bottom = min((y+1) * chunk_y, height)
            # box = (left, top, right, bottom)
            data = image.crop((left, top, right, bottom))
            chunkname = directory + "/" + str(count) + ".jpg"
            data.save(chunkname)
            size = os.stat(chunkname).st_size
            box = Box(left, top, right, bottom)
            chunk = Chunk(uuid4(), chunkname, size, box)
            chunks[chunk.uuid] = chunk
            count = count + 1
    return chunks

# stich chunks into image
def stichChunksIntoImage(directory, filename, metadata):
    width = 182
    height = 162

    print(metadata)
    # creates a new empty image, RGB mode, and size width by height
    result = Image.new('RGB', (width, height))

    count = 0 # chunk counter
    chunks = metadata[1]
    print(chunks)
    for chunk in chunks:
        # fetch the chunk
        if chunk.name[-6] == "/":
            data = Image.open(directory + chunk.name[-5] + ".jpg")
            print(chunk.box)
            result.paste(data, (chunk.box.left, chunk.box.top))
        else:
            data = Image.open(directory + chunk.name[-6:-5] + ".jpg")
            print(chunk.box)
            result.paste(data, (chunk.box.left, chunk.box.top))
    result.save(filename)
    return
