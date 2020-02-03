#!/usr/bin/env python3

import sys
import subprocess
import time


def run_fuo():
    popen = subprocess.Popen(['fuo', '-v'])
    time.sleep(5)
    subprocess.run(['fuo', 'exec', 'app.close()'])
    returncode = popen.wait(timeout=2)
    sys.exit(returncode)


if __name__ == '__main__':
    run_fuo()
