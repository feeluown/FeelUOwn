OS = $(shell lsb_release -si)
VER = $(shell lsb_release -sr)


dep:
	@echo "system version: ", $(OS), $(VER)
ifeq ($(OS),Ubuntu)
	sudo apt-get install python3-dbus
	sudo apt-get install python3-dbus.mainloop.pyqt5
else ifeq ($(OS), Deepin)
	@echo "no official support for your system"
endif

all: dep
