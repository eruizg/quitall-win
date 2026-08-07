"""PyInstaller entry point.

The package's own ``__main__.py`` uses relative imports (``from . import ...``)
which fail when PyInstaller runs that file as a top-level script — there's no
parent package in that mode. This thin shim sits *outside* the package, so
importing ``quitall_win.__main__`` works the regular way and the package's
own internal imports keep resolving normally.

For dev runs we still recommend ``python -m quitall_win`` — that path
doesn't need this file at all.
"""
from __future__ import annotations

import sys

from quitall_win.__main__ import main


if __name__ == "__main__":
    sys.exit(main())
