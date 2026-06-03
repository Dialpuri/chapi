"""Post-build smoke test for the coot_headless_api wheel.

Run by cibuildwheel (see [tool.cibuildwheel] test-command in pyproject.toml)
against each freshly built+repaired wheel, installed into an isolated venv.

It verifies that:
  * the package wrapper imports and re-exports the extension API,
  * __init__.py auto-set COOT_PREFIX to the bundled package directory,
  * the bundled share/coot data is actually usable (a monomer is built from
    the bundled CCP4 monomer dictionary).

Intentionally has no third-party dependencies so no test-requires are needed.
"""

import os
import sys

import coot_headless_api as coot

# 1. The package wrapper should re-export the extension's public API.
assert hasattr(coot, "molecules_container_t"), \
    "coot_headless_api did not re-export molecules_container_t"

# 2. __init__.py should have pointed COOT_PREFIX at the bundled data, unless an
#    explicit override was set in the environment.
if not os.environ.get("COOT_DATA_DIR"):
    prefix = os.environ.get("COOT_PREFIX")
    assert prefix, "COOT_PREFIX was not set by the package __init__.py"
    bundled = os.path.join(prefix, "share", "coot")
    assert os.path.isdir(bundled), f"bundled data dir missing: {bundled}"

# 3. The bundled data must be usable end to end. get_monomer reads the bundled
#    monomer dictionary (share/coot/lib/data/monomers) and returns a molecule
#    index >= 0 on success, or -1 if the dictionary could not be found/read.
mc = coot.molecules_container_t(False)
imol = mc.get_monomer("ALA")
assert imol >= 0, (
    f"get_monomer('ALA') returned {imol}; bundled monomer data was not loaded"
)

print(
    f"smoke test OK (python {sys.version_info.major}.{sys.version_info.minor}): "
    "import + COOT_PREFIX + bundled monomer data all working"
)
