#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from cli_hci import CliShell
from cli_hci import Helpers


if __name__ == "__main__":
    os.system('clear')
    cli = CliShell()
    Helpers.welcome()
    Helpers.show_title()
    if cli.connect_to_server(port=12100):
        cli.cmdloop()
