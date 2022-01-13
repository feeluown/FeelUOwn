.PHONY: docs


all: unittest

docs:
	cd docs && make html

pylint:
	pylint feeluown/gui/pages/ feeluown/fuoexec


MYPY_PKGS=
MYPY_PKGS+=feeluown/library/
MYPY_PKGS+=feeluown/player/
MYPY_PKGS+=feeluown/app/
MYPY_PKGS+=feeluown/entry_points/

mypy:
# Add flag --check-untyped-defs.
	mypy  ${MYPY_PKGS}
	mypy --check-untyped-defs feeluown/gui/widgets/textlist.py

flake8:
	flake8 fuocore/ feeluown/ tests/

# flake8 is mainly used for constrainting coding style
# pylint is mainly used for finding obvious bugs
# mypy is mainly used for better readable code
lint: flake8 mypy pylint

unittest: pytest

pytest:
	TEST_ENV=travis pytest -vv

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
