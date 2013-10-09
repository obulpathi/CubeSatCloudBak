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

spacelink:
	sudo tc qdisc add dev eth0 root netem rate 1mbit delay 5ms 2ms distribution normal loss 0.3% 25%

groundlink:
	sudo tc qdisc add dev eth0 root netem rate 10kbit delay 8ms 2ms distribution normal loss 1% 25%

resetlinks:
	sudo tc qdisc del dev eth0 root
	
install:
	echo "Install required software"
	sudo apt-get install python-twisted cython python-dev matplotlib numpy scipy python-pip
	sudo pip install -U scikit-image
	cd /usr/local/lib/python2.7/dist-packages
	sudo chown -R obulpathi:obulpathi *
