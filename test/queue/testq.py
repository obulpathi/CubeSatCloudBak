import Queue
import threading

queue = Queue.Queue()

def add():
    i = 0
    while i < 4:
        queue.put(i)
        i += 1

def remove():
    i = 0
    while i < 4:
        print queue.get()

if __name__ == '__main__':
    add()
    remove()
