LINT_FILES = fuocore/
LINT_FILES += feeluown/app.py
LINT_FILES += feeluown/ui.py
LINT_FILES += feeluown/task.py
LINT_FILES += feeluown/entry_points
LINT_FILES += feeluown/widgets/
LINT_FILES += tests/test_*_model.py

.PHONY: docs

all: unittest

docs:
	cd docs && make html

lint:
	flake8 $(LINT_FILES)

unittest: pytest

pytest:
	TEST_ENV=travis pytest

test: lint unittest

clean:
	find . -name "*~" -exec rm -f {} \;
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*flymake.py" -exec rm -f {} \;
	find . -name "\#*.py\#" -exec rm -f {} \;
	find . -name ".\#*.py\#" -exec rm -f {} \;
	find . -name __pycache__ -delete
