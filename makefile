run:
	python3 -m feeluown -d

test:
	PYTHONPATH=~/code/FeelUOwn/feeluown/plugins: py.test-3.4
