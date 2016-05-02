run:
	python3 -m feeluown -d

test:
	PYTHONPATH=~/code/FeelUOwn/feeluown/plugins:$PYTHONPATH py.test-3.4

try:
	PYTHONPATH=~/code/FeelUOwn/feeluown/plugins:$PYTHONPATH ipython3
	
