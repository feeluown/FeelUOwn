#!/usr/bin/env python

import json
from enum import Enum

from PyQt5.QtGui import QColor


class ColorName(Enum):
    # Normal.
    black = 'ansi_0_color'
    red = 'ansi_1_color'
    yellow = 'ansi_2_color'
    green = 'ansi_3_color'
    blue = 'ansi_4_color'
    magenta = 'ansi_5_color'
    cyan = 'ansi_6_color'
    white = 'ansi_7_color'

    # Bright.
    b_black = 'ansi_8_color'
    b_red = 'ansi_9_color'
    b_yellow = 'ansi_10_color'
    b_green = 'ansi_11_color'
    b_blue = 'ansi_12_color'
    b_magenta = 'ansi_13_color'
    b_cyan = 'ansi_14_color'
    b_white = 'ansi_15_color'

    background = 'background_color'
    foreground = 'foreground_color'
    bold = 'bold_color'
    cursor = 'cursor_color'
    cursor_text = 'cursor_text_color'
    selected = 'selection_color'
    selected_text = 'selected_text_color'


def read_xrdb(filepath):
    xrdb = {}
    with open(filepath) as f:
        for line in f:
            _, name, color = line.split(' ')
            name, color = name.strip().lower(), color.strip()
            try:
                xrdb[ColorName(name)] = color
            except ValueError:
                print(f"unknown color name '{name}'")
    return xrdb


def active_colors(xrdb):
    foreground = xrdb[ColorName.foreground]
    background = xrdb[ColorName.background]

    role_color_dict = {
        'Background': background,
        'Window': background,
        'WindowText': foreground,
        'Text': foreground,
        'Foreground': foreground,

        # According to qpalette docs, role and color have following mapping.
        'Link': xrdb[ColorName.b_blue],
        'LinkVisited': xrdb[ColorName.b_magenta],
        'Highlight': xrdb[ColorName.blue],
        'HighlightedText': xrdb[ColorName.b_white],
        'PlaceholderText': foreground,

        # The following mapping are decided according to experience (by cosven),
        # which may be not accurate.
        'Base': xrdb[ColorName.black],  # Same as the background.
        'AlternateBase': xrdb[ColorName.black],  # Usually similar to background.
        'BrightText': xrdb[ColorName.b_white],

        'ButtonText': foreground,

        # I found the button is usually lighter than the background.
        'Button': xrdb[ColorName.black],
        # Based on Button and following the qpalette rules,
        # we choose colors for light.
        'Light': xrdb[ColorName.b_black],
        'MidLight': xrdb[ColorName.b_black],  # No corresponding color.
        'Dark': xrdb[ColorName.background],
        'Mid': xrdb[ColorName.background],   # No corresponding color.

        'Shadow': xrdb[ColorName.black],
        'NoRole': xrdb[ColorName.black],

        'ToolTipBase': xrdb[ColorName.black],
        'ToolTipText': foreground,
    }
    return role_color_dict


def inactive_colors(xrdb):
    colors = active_colors(xrdb)
    colors['Highlight'] = QColor(xrdb[ColorName.blue]).darker(130).name()
    return colors


def disabled_colors(xrdb):
    colors = active_colors(xrdb)
    # Lighter than the base.
    colors['Highlight'] = QColor(xrdb[ColorName.blue]).lighter(150).name()
    # A color similar to background.
    colors['ButtonText'] = QColor(xrdb[ColorName.background]).lighter(150).name()
    return colors


def read_termlike_colors(name):
    xrdb = read_xrdb(f'feeluown/gui/assets/themes/xrdb/{name}.xrdb')
    colors = {
        "Active": active_colors(xrdb),
        "Disabled": disabled_colors(xrdb),
        "Inactive": inactive_colors(xrdb)
    }
    return colors


if __name__ == '__main__':
    pass
