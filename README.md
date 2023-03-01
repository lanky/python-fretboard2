<!-- vim: set nofen :-->
# python-fretboard2

This is a (possibly backwards-incompatible) fork of Derek Payton's
python-fretboard, with the changes we wanted for our ukulele songsheets.

This includes

* styling (CSS, SVG template) changes
* additional classes
* dynaconf support
* refactoring and linting (black, flake8)
* poetry build/configuration
* pre-commit
* python 3.10+ type hints

All the changes we applied since the start of our derivative project are being
applied here. The hope is to end up with a maintainable codebase, with modern
build configurations and tests.

The original  [README](README.orig.rst) file is here for more documentation.
