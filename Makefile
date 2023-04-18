.PHONY: docs


all: unittest

docs:
	cd docs && make html

PYLINT_PKGS=
PYLINT_PKGS+=feeluown/gui/pages/
PYLINT_PKGS+=feeluown/gui/uimodels/
PYLINT_PKGS+=feeluown/fuoexec/
PYLINT_PKGS+=feeluown/server/
PYLINT_PKGS+=feeluown/collection.py
pylint:
	pylint ${PYLINT_PKGS}

# Packages need to check currently.
# All packages are supposed to be checked in the future.
MYPY_PKGS=
MYPY_PKGS+=feeluown/library/
MYPY_PKGS+=feeluown/player/
MYPY_PKGS+=feeluown/app/
MYPY_PKGS+=feeluown/entry_points/
MYPY_STRICT_PKGS=
MYPY_STRICT_PKGS+=feeluown/collection.py
MYPY_STRICT_PKGS+=feeluown/utils/reader.py
MYPY_STRICT_PKGS+=feeluown/server/
MYPY_STRICT_PKGS+=feeluown/cli/cli.py
MYPY_STRICT_PKGS+=feeluown/gui/
mypy:
# Add flag --check-untyped-defs.
# On GitHub Actions environment, there maybe another mypy executable.
# To prevent unexpected behavior, use 'python -m mypy' to ensure
# the right mypy is used.
	which python
	mypy -V
	python -m mypy -V
	python -m mypy -vv ${MYPY_PKGS}
	python -m mypy --check-untyped-defs ${MYPY_STRICT_PKGS}

flake8:
	flake8 feeluown/ tests/

# flake8 is mainly used for constrainting coding style
# pylint is mainly used for finding obvious bugs
# mypy is mainly used for better readable code
lint: flake8 mypy pylint

unittest: pytest

pytest:
	TEST_ENV=travis QT_QPA_PLATFORM=offscreen pytest

integration_test: export QT_QPA_PLATFORM=offscreen
integration_test:
	./integration-tests/run.py

test: lint unittest

# Please install pyinstaller manually.
bundle:
	pyinstaller -w feeluown/pyinstaller/main.py \
		--icon feeluown/gui/assets/icons/feeluown.ico \
		--name FeelUOwn \
		-w \
		--noconfirm

clean:
	find . -name "*~" -exec rm -f {} \;
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*flymake.py" -exec rm -f {} \;
	find . -name "\#*.py\#" -exec rm -f {} \;
	find . -name ".\#*.py\#" -exec rm -f {} \;
	find . -name __pycache__ -delete
