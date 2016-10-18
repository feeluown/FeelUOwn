run:
	python3 -m feeluown -d

test:
	PYTHONPATH=./feeluown/plugins: py.test-3.4

try:
	PYTHONPATH=./feeluown/plugins: ipython3
	
install:
	sudo ./install.py
