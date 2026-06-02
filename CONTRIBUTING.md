# Contributing to chapi

## Repo layout

```
chapi/
├── coot/                    # Coot submodule (upstream source)
├── patches/                 # Patches applied to coot/ and its deps
├── get_sources              # Script that fetches/builds all dependencies
├── generate_docstring_cache.py  # Generates C++ docstring cache from Doxygen XML
├── pyproject.toml           # Build config (scikit-build-core + cibuildwheel)
├── fftw/  rfftw/  fftw3/   # FFTW 2 (single/double) and FFTW 3 — CMake wrappers
├── ccp4/  mmdb2/  ssm/     # CCP4 library CMake wrappers
├── clipper/                 # Clipper CMake wrapper
├── gemmi/                   # Gemmi CMake wrapper
├── checkout/                # Populated at build time by get_sources
└── build_wheel/             # CMake build directory (git-ignored)
```

`coot` is a git submodule pointing to a specific upstream commit. All other dependencies are either git-cloned or downloaded by `get_sources` into `checkout/` at build time.

## How the build works

The package is built with **scikit-build-core**, which drives CMake from `pyproject.toml`. The CMake source is `coot/CMakeLists.txt`, but that file is patched (see below) to detect the `SKBUILD` flag set by scikit-build-core.

When `SKBUILD` is set, `coot/CMakeLists.txt` builds all dependencies from source (the directories at repo root: `fftw`, `rfftw`, `fftw3`, `mmdb2`, `ccp4`, `gemmi`, `ssm`, `clipper/*`). When `SKBUILD` is not set, it expects those libraries to already be installed system-wide (the normal Coot developer workflow).

The only targets built for the wheel are `coot_headless_api` (the nanobind extension) and `coot_headless_api_ext_stub` (the `.pyi` stub).

### Before the build

`pyproject.toml`'s `before-all` step runs `get_sources`, which:

1. Applies patches idempotently to the `coot` submodule.
2. Clones/downloads all dependencies into `checkout/` if not already present.
3. On Linux, builds RDKit `Release_2024_09_5` from source into `/opt/rdkit` (skipped if already present).

RDKit is cached across CI runs — see [CI caching](#ci-and-caching) below.

### Docstring cache

Coot's nanobind bindings serve docstrings from Doxygen XML. To avoid shipping the XML in the wheel, `generate_docstring_cache.py` is run in `before-all` after Doxygen:

```
doxygen coot-api-dox.cfg   →   classmolecules__container__t.xml
generate_docstring_cache.py →  coot/api/molecules-container-docstrings-cache.cc
```

The generated `.cc` file defines `fill_docstring_cache()`, which the nanobind module calls on first use instead of parsing XML at runtime. The script is a faithful port of the C++ XML-parsing logic so the output is identical.

## Patches

`patches/` contains patches for the `coot` submodule and some of its dependencies:

| Patch | What it does |
|-------|-------------|
| `coot-cmakelists.patch` | Adds `SKBUILD` guards so all deps are built from source when building the wheel |
| `coot-nanobind-docstrings.patch` | Wires in `fill_docstring_cache()` so the build-time cache is used instead of runtime XML parsing |
| `clipper-*.patch` | C++20 and header fixes for Clipper |
| `fftw3-version-patch.patch` | Bumps `cmake_minimum_required` in FFTW3's CMakeLists |

Patches are applied by `get_sources` and are idempotent — re-running `get_sources` will not re-apply an already-applied patch.

### Updating a patch

```bash
# Make your edits inside coot/
git -C coot diff > patches/coot-cmakelists.patch   # regenerate the patch
```

If you update the `coot` submodule to a new upstream commit, verify all patches still apply cleanly before committing.

## CI and caching

Wheels are built with **cibuildwheel** via `.github/workflows/wheels.yml`. The matrix covers `macos-latest`, `ubuntu-latest` (x86_64), and `ubuntu-24.04-arm` (aarch64). Only CPython 3.13 (`cp313-*`) is built.

### RDKit cache (Linux only)

On macOS, RDKit comes from Homebrew bottles (fast). On Linux, it is compiled from source which takes ~15 minutes. The workflow caches the compiled install:

- **Cache key:** `rdkit-Release_2024_09_5-<matrix.os>`
- **Cached path:** `rdkit-install/` in the workspace root
- **Mechanism:** `before-all` copies `rdkit-install/` → `/opt/rdkit` before `get_sources` runs. If that copy exists, `get_sources` detects `/opt/rdkit/lib/libRDKitRDGeneral.so` and skips the build. After a fresh build, `before-all` copies `/opt/rdkit` → `rdkit-install/` so `actions/cache` can save it.

If you bump the RDKit version in `get_sources`, update the cache key in `wheels.yml` to match, otherwise the old cached build will be used.

### Triggering a release

The workflow runs on any `v*` tag push and uploads to PyPI automatically. For a test upload, trigger it manually via **workflow_dispatch** and select `testpypi`.

## Local development

To build locally, run `get_sources` first (it is idempotent):

```bash
bash ./get_sources
pip install --no-build-isolation -e .
```

On macOS, install system dependencies first:

```bash
brew install gsl boost libpng rdkit expat doxygen
```

On Linux, see the `before-all` list in `pyproject.toml` for the required packages.
