import os
import Image

directory = "images/"

images = os.listdir(directory)
for image in images:
    filename = directory + image
    image = Image.open(filename)
    width = image.size[0]
    height = image.size[1]
    data = image.crop((0, 0, width, height))
    data.save(filename)
