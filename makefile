run:
	python3 -m feeluown -d

unittest:
	PYTHONPATH=./feeluown/plugins: coverage run --source=feeluown setup.py test && coverage report -m

test: unittest
	PYTHONPATH=./feeluown/plugins: python setup.py test

try:
	PYTHONPATH=./feeluown/plugins: ipython3

install:
	sudo ./install.py
