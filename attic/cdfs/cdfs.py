import math
import uuid
import os
import time
import operator

def main():
    # test script for filesystem

    # setup
    master = CDFSMaster()
    client = CDFSClient(master)

    # test write, exist, read
    print "\nWriting..."
    client.write("/usr/python/readme.txt", """
        This file tells you all about python that you ever wanted to know.
        Not every README is as informative as this one, but we aim to please.
        Never yet has there been so much information in so little space.
        """)
    print "File exists? ", client.exists("/usr/python/readme.txt")
    print client.read("/usr/python/readme.txt")

    # test append, read after append
    print "\nAppending..."
    client.write_append("/usr/python/readme.txt", \
        "I'm a little sentence that just snuck in at the end.\n")
    print client.read("/usr/python/readme.txt")

    # test delete
    print "\nDeleting..."
    client.delete("/usr/python/readme.txt")
    print "File exists? ", client.exists("/usr/python/readme.txt")
    
    # test exceptions
    print "\nTesting Exceptions..."
    try:
        client.read("/usr/python/readme.txt")
    except Exception as e:
        print "This exception should be thrown:", e
    try:
        client.write_append("/usr/python/readme.txt", "foo")
    except Exception as e:
        print "This exception should be thrown:", e

    # show structure of the filesystem
    print "\nMetadata Dump..." 
    print master.dump_metadata()

if __name__ == "__main__":
    main()
