import sys
import os


if __name__ == '__main__':
    # Chdir first and then load feeluown, so that libmpv can be loaded correctly.
    # On macOS, the dir is changed to FeelUOwnX.app/Contents/Frameworks.
    if hasattr(sys, '_MEIPASS'):
        os.chdir(sys._MEIPASS)

    import feeluown.__main__

    os.environ.setdefault('FUO_LOG_TO_FILE', '1')
    feeluown.__main__.main()
