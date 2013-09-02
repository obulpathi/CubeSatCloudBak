import uuid
import pickle

from cloud.common import Packet

metadata = {1:"one", 2:"two", 3:"three", 4:["one", "two", "three", "four"]}

# print data
packet = Packet(1, "Receiver", 1, "Server", "METADATA", metadata, "headers_size")
print packet
packetstring = pickle.dumps(packet)
new_packet = pickle.loads(packetstring)
print new_packet
