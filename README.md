# coot_headless_api

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

## Quick start

```python
import coot_headless_api as coot

mc = coot.molecules_container_t(False)

# Load a model and map
imol     = mc.read_pdb("model.pdb")
imol_map = mc.auto_read_mtz("data.mtz")

# Real-space refinement
mc.refine_residues_using_atom_cid(imol, "//A/1-10", "TRIPLE", False)

# Fit a ligand
mc.import_cif_dictionary("ligand.cif", -999999)
mc.fit_to_map_by_random_jiggle_using_cid(imol, "//A/LIG", imol_map, 100, 1.0)

# Write out the result
mc.write_coordinates(imol, "refined.pdb")
```

## Key functionality

### I/O
```python
imol = mc.read_pdb("model.pdb")           # Load a model
mc.write_coordinates(imol, "out.pdb")      # Save a model
imol_map = mc.auto_read_mtz("data.mtz")   # Load reflections (auto-detects columns)
mc.import_cif_dictionary("LIG.cif", imol)  # Load a ligand dictionary
```

### Refinement
```python
# Refine a residue range by CID selection
mc.refine_residues_using_atom_cid(imol, "//A/1-50", "TRIPLE", False)

# Refine with a specific map
mc.set_imol_refinement_map(imol_map)
mc.refine_residues(imol, [coot.residue_spec_t("A", 42, "")])
```

### Validation
```python
vi = mc.density_fit_analysis(imol, imol_map)
rama = mc.ramachandran_analysis(imol)
rota = mc.rotamer_analysis(imol)
```

### Superposition
```python
mc.SSM_superpose(imol_ref, "//A", imol_mov, "//A")
```

### Ligand fitting
```python
mc.import_cif_dictionary("ligand.cif", -999999)
mc.fit_to_map_by_random_jiggle_using_cid(imol, "//A/LIG", imol_map, 100, 1.0)
```

### 3D mesh export
```python
# Export model, map, or contact dots as glTF for 3D visualisation
mc.export_model_molecule_as_gltf(imol, "//A", "bonds", False, 0.1, "model.glb")
mc.export_map_molecule_as_gltf(imol_map, 0.0, 0.0, 0.0, 20.0, 0.35, "map.glb")
```

## Notes

- `molecules_container_t(verbose)` — pass `False` to suppress log output
- Molecule indices returned by `read_pdb` / `auto_read_mtz` are used as handles in all subsequent calls
- CID (Crystallographic Identifier) strings follow the format `//chain/residue-range/atom`; e.g. `"//A/42"`, `"//A/1-100"`, `"//A/42/CA"`

## Related packages

- [**Moorhen**](https://github.com/pemsley/coot) — browser-based Coot, uses the same underlying API via WebAssembly

## License

GPLv3 — see [Coot's licence](https://github.com/pemsley/coot/blob/main/COPYING) for details.
