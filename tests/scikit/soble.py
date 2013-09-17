from skimage import data, io, filter

image = data.coins() # or any NumPy array!
edges = filter.sobel(image)
io.imshow(edges)
