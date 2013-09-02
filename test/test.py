import uuid
import pickle

from cloud.common import Packet
from cloud.common import Work

# Sender: 1, Receiver: Receiver, Source: 1, Destination: Server, CHUNK, Payload: uuid: 3ef1d6c0-5ead-4f0b-a05f-7e6ebce331ca, job: DOWNLINK, filename: 196.jpg, Size: 22
data = open("/home/obulpathi/phd/cloud/data/1/83.jpg").read()
work = Work(uuid.uuid4(), "DOWNLINK", "196.jpg", data)
# print data
packet = Packet(1, "Receiver", 1, "Server", "CHUNK", work, "headers_size")
print packet
packetstring = pickle.dumps(packet)
new_packet = pickle.loads(packetstring)
print new_packet
