class Packet(object):
    def __init__(self, data):
        self.data = data
    def __repr__(self):
        return "Packet: " + self.data

p = Packet("1234")
print str(p)
