import pickle
from cloud.transport.transport import MyTransport

stringa = """abcI am using texlive 2010 and texworks. My problem is that missfont.log file is created in my home directory. The followings are generated in log file

mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 cmr10
mktextfm cmr10
mktexpk --mfmode / --bdpi 600 --mag 1+0/600 --dpi 600 cmr10
mktextfm cmr10


This file is created whenever i run latex. My operating system is ubuntu 10.04

It looks like you have an unconfigured or partially-installed TeX system. CM fonts come as Type 1 these days: the MF versions are not normally used. Try running sudo update-updmap to get the fonts recognised first, then run updmap to enable them. Then run texconfig in an xterm window and make sure it is configured properly for your printer etc."""

stringb = """def"""

class TestClass(object):
    def __init__(self):
        pass
    def packetReceived(self, string):
        if string == stringa:
            print("String A")
        elif string == stringb:
            print("String B")
        else:
            print(string)

testClass = TestClass()

transport = MyTransport(testClass)
picklestringa = pickle.dumps(stringa)
codedpicklestringa = str(len(picklestringa)).zfill(6) + picklestringa
#print(picklestringa)
#print(codedpicklestringa[6:])
#print(codedpicklestringa)
picklestringb = pickle.dumps(stringb)
codedpicklestringb = str(len(picklestringb)).zfill(6) + picklestringb
picklestring = codedpicklestringa + codedpicklestringb
print("Lengths")
print(len(codedpicklestringa))
print(len(codedpicklestringb))
print(len(picklestring))
transport.dataReceived(picklestring)
transport.dataReceived(picklestring)
transport.dataReceived(picklestring)
