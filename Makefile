.PHONY: docs


all: unittest

docs:
	cd docs && make html

PYLINT_PKGS=
PYLINT_PKGS+=feeluown/gui/pages/
PYLINT_PKGS+=feeluown/gui/uimodels/
PYLINT_PKGS+=feeluown/gui/widgets/lyric.py
PYLINT_PKGS+=feeluown/fuoexec/
PYLINT_PKGS+=feeluown/server/
PYLINT_PKGS+=feeluown/gui/components/
PYLINT_PKGS+=feeluown/nowplaying/
PYLINT_PKGS+=feeluown/collection.py
PYLINT_PKGS+=feeluown/plugin.py
PYLINT_PKGS+=feeluown/player/lyric.py
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
	mypy ${MYPY_PKGS}
	mypy --check-untyped-defs ${MYPY_STRICT_PKGS}

# mypy has several issues:
# 1. mypy behaves inconsistently between local and CI environments.
# 2. mypy checks other files even if only one file is specified.
#
# So give pyright a try.
PYRIGHT_PKGS=
PYRIGHT_PKGS+=feeluown/gui/uimain/sidebar.py
PYRIGHT_PKGS+=feeluown/gui/uimain/provider_bar.py
pyright:
	pyright ${PYRIGHT_PKGS}

flake8:
	flake8 feeluown/ tests/

# flake8 is mainly used for constrainting coding style
# pylint is mainly used for finding obvious bugs
# mypy is mainly used for better readable code
lint: flake8 pylint

unittest: pytest

pytest:
# Disable faulthandler plugin, because it cause verbose output on windows.
# Besides, the fault currently cause no side effects.
	TEST_ENV=travis QT_QPA_PLATFORM=offscreen pytest -p no:faulthandler

integration_test: export QT_QPA_PLATFORM=offscreen
integration_test:
	./integration-tests/run.py

test: lint unittest

BUNDLE_FLAGS=
# On macOS, excluding the following moduels can decrease the package size by 130MB,
# mainly due to the QtWebEngine module.
BUNDLE_FLAGS += --exclude PyQt5.QtQml
BUNDLE_FLAGS += --exclude PyQt5.QtDBus
BUNDLE_FLAGS += --exclude PyQt5.QtPdf
BUNDLE_FLAGS += --exclude PyQt5.QtQuick
BUNDLE_FLAGS += --exclude PyQt5.QtNetwork
BUNDLE_FLAGS += --exclude PyQt5.QtWebEngineCore
BUNDLE_FLAGS += --exclude PyQt5.QtWebEngineWidgets

ifeq ($(OS),Windows_NT)
	BUNDLE_FLAGS += --name FeelUOwn
	BUNDLE_FLAGS += --icon feeluown/gui/assets/icons/feeluown.ico
	BUNDLE_FLAGS += --version-file version_file.txt
else
# macOS: since apfs is not case-sensitive, we use FeelUOwnX instead of FeelUOwn
	BUNDLE_FLAGS += --name FeelUOwnX --osx-bundle-identifier org.feeluown.FeelUOwnX
	BUNDLE_FLAGS += --icon feeluown/gui/assets/icons/feeluown.icns
endif

# Please install pyinstaller manually.

ifeq ($(OS),Windows_NT)
bundle:
	create-version-file .metadata.yml --version \
		$(shell python -c 'print(__import__("feeluown").__version__, end="")' | tr -c '[:digit:]' '.')
	pyinstaller -w feeluown/pyinstaller/main.py \
		${BUNDLE_FLAGS} \
		-w \
		--noconfirm
else
bundle:
	pyinstaller -w feeluown/pyinstaller/main.py \
		${BUNDLE_FLAGS} \
		-w \
		--noconfirm
endif

clean: clean_py clean_emacs

clean_py:
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name __pycache__ -delete
	find . -name .mypy_cache/ -delete

clean_emacs:
	find . -name "*~" -exec rm -f {} \;
	find . -name "*flymake.py" -exec rm -f {} \;
	find . -name "\#*.py\#" -exec rm -f {} \;
	find . -name ".\#*.py\#" -exec rm -f {} \;
