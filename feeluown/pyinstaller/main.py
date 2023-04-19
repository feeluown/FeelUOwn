import sys
import os
import feeluown.__main__


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)

    feeluown.__main__.main()
