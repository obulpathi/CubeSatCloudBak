#! /usr/bin/env python

import time
import utils

images = ["1.jpg", "2.jpg"]

if __name__ == "__main__":
    for image in images:
        t1 = time.time()
    	data = utils.read("images/" + image)
    	utils.write("results/" + image, data)
    	t2 = time.time()
    	print "Image: " + image, "  Time: ", (t2-t1)
