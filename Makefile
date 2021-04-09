.PHONY: docs

all: unittest

docs:
	cd docs && make html

# flake8 is mainly used for constrainting coding style
# pylint is mainly used for finding obvious bugs
# mypy is mainly used for better readable code
lint:
	flake8 fuocore/ feeluown/ tests/
	pylint feeluown/gui/pages/
	mypy feeluown/library feeluown/player

unittest: pytest

pytest:
	TEST_ENV=travis pytest

integration_test:
	./integration-tests/run.py

test: lint unittest

clean:
	find . -name "*~" -exec rm -f {} \;
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*flymake.py" -exec rm -f {} \;
	find . -name "\#*.py\#" -exec rm -f {} \;
	find . -name ".\#*.py\#" -exec rm -f {} \;
	find . -name __pycache__ -delete
