"""Headless API for Coot.

This package is a thin wrapper around the compiled ``coot_headless_api``
extension module. Its only job before handing control to the extension is to
tell Coot where to find its runtime data.

The wheel bundles Coot's data files under ``<package>/share/coot``. Coot's C++
layer locates them via ``coot::package_data_dir()``, which honours the
``COOT_PREFIX`` / ``COOT_DATA_DIR`` environment variables. We set
``COOT_PREFIX`` to this package directory here, *before* importing the
extension. Assigning to ``os.environ`` updates the process environment through
``setenv()``, so the C++ ``getenv()`` sees the value. An explicit user/system
override is left untouched.
"""

import os as _os

_pkg_dir = _os.path.dirname(_os.path.abspath(__file__))

if not _os.environ.get("COOT_PREFIX") and not _os.environ.get("COOT_DATA_DIR"):
    # Only adopt the bundled prefix if the data is actually present, so a
    # layout without bundled data falls back to the compile-time PKGDATADIR.
    if _os.path.isdir(_os.path.join(_pkg_dir, "share", "coot")):
        _os.environ["COOT_PREFIX"] = _pkg_dir

# Re-export the extension module's public API as the package's own API, so
# ``import coot_headless_api`` behaves exactly like importing the bare module.
from .coot_headless_api import *  # noqa: E402,F401,F403
from . import coot_headless_api as _ext  # noqa: E402
from .__version__ import __version__  # noqa: E402,F401
