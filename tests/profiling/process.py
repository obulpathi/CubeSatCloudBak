#! /usr/bin/env python

import os
import time
import Image
import ImageFilter

images = ["1.jpg", "2.jpg"]

if __name__ == "__main__":
    for filename in images:
        t1 = time.time()
        image = Image.open("images/" + filename)
        # invert image (obtain negative)
        # nimage = ImageChops.invert(image)
        # apply BLUR filter
        # imageBlur = image.filter(ImageFilter.BLUR)
        # apply CONTOUR filter
        # imageContour = image.filter(ImageFilter.CONTOUR)
        # apply DETAIL filter
        # imageDetail = image.filter(ImageFilter.DETAIL)
        # apply EDGE_ENHANCE filter
        # imageEdgeEnhance = image.filter(ImageFilter.EDGE_ENHANCE)
        # apply EDGE_ENHANCE_MORE filter
        # imageEdgeEnhanceMore = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        # apply EMBOSS filter
        # imageEmboss = image.filter(ImageFilter.EMBOSS)
        # apply FIND_EDGES filter
        # imageEdges = image.filter(ImageFilter.FIND_EDGES)
        # apply SMOOTH filter
        # imageSmooth = image.filter(ImageFilter.SMOOTH)
        # apply SMOOTH_MORE filter
        # imageSmoothMore = image.filter(ImageFilter.SMOOTH_MORE)
        # apply SHARPEN filter
        # imageSharp = image.filter(ImageFilter.SHARPEN)
        edges = image.filter(ImageFilter.FIND_EDGES)
        edges.save("results/" + os.path.split(filename)[1])
    	t2 = time.time()
    	print "Image: " + filename, "  Time: ", (t2-t1)
