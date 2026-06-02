# coot_headless_api (chapi)

Python bindings for [Coot](https://www2.mrc-lmb.cam.ac.uk/personal/pemsley/coot/)'s **libcootapi** — a headless, scriptable interface to Coot's macromolecular model-building and refinement engine.

## Overview

Coot is the standard tool for macromolecular model building in X-ray and cryo-EM crystallography. This package exposes Coot's core API as a Python extension module, allowing you to run model building, refinement, validation and ligand fitting programmatically — without a display or GUI.

The central class is `molecules_container_t`, which manages a collection of molecular models and electron density maps and provides methods to operate on them.

## Installation

```bash
pip install coot_headless_api
```

### Platform support

| Platform       | Supported |
|----------------|-----------|
| macOS (arm64)  | ✅ macOS 15+ |
| Linux (x86_64) | ✅ glibc 2.34+ (Ubuntu 22.04+) |
| Linux (aarch64)| ✅ glibc 2.34+ (Ubuntu 22.04+) |
| Windows        | ❌ |

## Getting started

To get started, take a look at the [coot-headless-api documentation](https://www.mrc-lmb.cam.ac.uk/lucrezia/libcootapi-documentation/index.html).



## Related packages

- [**Moorhen**](https://github.com/pemsley/coot) — browser-based Coot, uses the same underlying API via WebAssembly

## License

GPLv3 — see [Coot's licence](https://github.com/pemsley/coot/blob/main/COPYING) for details.
