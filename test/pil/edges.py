import Image
import ImageFilter

image = Image.open("image.jpg")
edges = image.filter(ImageFilter.FIND_EDGES)
edges.save("edges.jpg")
