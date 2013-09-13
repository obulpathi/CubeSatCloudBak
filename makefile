all:
	rm -rf ~/phd/cloud/data/*
	python simulator.py

torrent:
	echo "execute torrent mission"

mapreduce:
	echo "execute mapreduce mission"

clean:
	rm -rf ~/phd/cloud/data/*

bootstrap:
	mkdir ~/phd/cloud/data

limit:
	echo "set netowrk speed limits"

install:
	echo "Install required software"
	sudo apt-get install python-twisted
