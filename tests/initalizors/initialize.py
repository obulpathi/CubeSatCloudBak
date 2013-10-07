class Box(object):
    def __init__(self, initstr):
        fields = initstr.split(":")
        x = int(fields[0])
        y = int(fields[1])
        
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __repr__(self):
        return str(self.x) + ":" + str(self.y)

if __name__ == "__main__":
    box = Box(2, 4)
    initstr = str(box)
    newBox = Box(initstr)
