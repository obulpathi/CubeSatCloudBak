import math

filename = "image.jpg"

MAX_PACKET_SIZE = 1000
image = open(filename, "r")
data = image.read()
length = len(data)
print "Size of image is :", length

print "fragmenting now"
fragments = []
for i in range(int(math.ceil(float(length)/MAX_PACKET_SIZE))):
    fragments.append(data[i*MAX_PACKET_SIZE:(i+1)*MAX_PACKET_SIZE])

print "Number of fragments: ", len(fragments)
print "stiching now"
packet = None
for fragment in fragments:
    if not packet:
        packet = fragment
    else:
        packet = packet + fragment

if packet == data:
    print "YEY"
else:
    print ":("
