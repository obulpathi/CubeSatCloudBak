import pickle
from cloud.core.common import Packet

packet = Packet("sender", "receiver", "source", "destination", "flags", "paylod", "headers_size")
packetstring = pickle.dumps(packet)
new_packet = pickle.loads(packetstring)
print new_packet
