from skimage import data, io, filter
import time

t1 = time.time()
image = data.coins() # or any NumPy array!
edges = filter.sobel(image)
t2 = time.time()
print (t2-t1)
io.imshow(edges)
