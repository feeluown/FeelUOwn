run:
	python3 -m feeluown -d

unittest:
	PYTHONPATH=./feeluown/plugins: pytest

test: unittest
	PYTHONPATH=./feeluown/plugins: pytest

try:
	PYTHONPATH=./feeluown/plugins: ipython3

install:
	sudo ./install.py
