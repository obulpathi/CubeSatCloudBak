from multiprocessing import Process , Pipe , Queue

# a , b = Pipe()
q = Queue()

def f(name):
    i = 0
    while i < 4:
        q.put(i)
        i += 1

def t():
    i = 0
    while i < 4:
        print q.get()

if __name__ == '__main__':
    p = Process(target=f, args=('bob',))
    p.start()
    p.join()
    p1 = Process(target=t, args= (''))
    p1.start()
    p1.join()
