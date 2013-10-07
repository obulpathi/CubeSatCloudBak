all:
	rm -rf ~/cloud/data/*
	python simulator.py

torrent:
	echo "execute torrent mission"

mapreduce:
	echo "execute mapreduce mission"

clean:
	rm -rf ~/cloud/data/*

bootstrap:
	mkdir ~/cloud/data/

limit:
	echo "set netowrk speed limits"

install:
	echo "Install required software"
	sudo apt-get install python-twisted cython python-dev matplotlib numpy scipy python-pip
	sudo pip install -U scikit-image
	cd /usr/local/lib/python2.7/dist-packages
	change permisssions
