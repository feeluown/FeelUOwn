"""
Make `python -m feeluown` an alias for running `fuo`.
"""


from feeluown.entry_points.run import run


main = run


if __name__ == '__main__':
    run()
