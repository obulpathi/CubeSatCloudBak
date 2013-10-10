.PHONY: clean chunks profile

clean:
	rm -rf output/*
	rm -rf results/*
	rm -rf chunks/*

chunks:
	python generateChunks.py

subchunks:
	python generateSubchunks.py

profile:
	python profile.py

profileread:
	python profileread.py

profilewrite:
	python profilewrite.py

profileprocess:
	python profileprocess.py
