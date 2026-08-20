"""Bundle OSPRay into an auditwheel-repaired manylinux wheel, names intact.

auditwheel renames every library it grafts (libfoo.so.1 -> libfoo-<hash>.so.1) and
patches the DT_NEEDED entries to match. That breaks OSPRay, which at ospInit() time
dlopen()s its CPU device *by file name*, in the directory it finds libospray in:

    could not open module lib ospray_module_cpu:
    .../coot_headless_api.libs/libospray_module_cpu.so.3.2.0: No such file or directory

So the OSPRay set is excluded from auditwheel (see repair-wheel-command in
pyproject.toml) and copied in here under its real names, with RPATH $ORIGIN so the
libraries resolve each other from the same directory.

Usage: python bundle_ospray_linux.py <wheel-dir> <ospray-prefix>
"""

import base64
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# The whole OSPRay runtime: OSPRay itself, its CPU device, Open VKL, Embree,
# rkcommon and TBB. Keep in sync with the --exclude patterns in pyproject.toml.
PATTERNS = ("libospray*.so*", "libopenvkl*.so*", "librkcommon*.so*",
            "libembree*.so*", "libtbb*.so*")

# OSPRay asks for its CPU device by full version, not by SONAME, so that name has
# to exist as a file of its own (wheels cannot carry symlinks).
DLOPENED_BY_FULL_NAME = "libospray_module_cpu"


def soname(path):
    out = subprocess.run(["patchelf", "--print-soname", str(path)],
                         capture_output=True, text=True, check=False)
    return out.stdout.strip() or path.name


def collect(ospray_prefix):
    """Map {file name in the wheel: real library on disk}."""
    wanted = {}
    for lib_dir in (Path(ospray_prefix) / "lib64", Path(ospray_prefix) / "lib"):
        if not lib_dir.is_dir():
            continue
        for pattern in PATTERNS:
            for lib in lib_dir.glob(pattern):
                if lib.is_symlink() or not lib.is_file():
                    continue
                # The SONAME is what the DT_NEEDED entries ask for.
                wanted[soname(lib)] = lib
                if lib.name.startswith(DLOPENED_BY_FULL_NAME):
                    wanted[lib.name] = lib
    return wanted


def record_line(root, path):
    data = path.read_bytes()
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return f"{path.relative_to(root).as_posix()},sha256={digest},{len(data)}\n"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    wheel_dir, ospray_prefix = Path(sys.argv[1]), Path(sys.argv[2])

    wheels = sorted(wheel_dir.glob("*.whl"), key=lambda p: p.stat().st_mtime)
    if not wheels:
        sys.exit(f"no wheel found in {wheel_dir}")
    wheel = wheels[-1]

    libs = collect(ospray_prefix)
    if not libs:
        sys.exit(f"no OSPRay libraries found under {ospray_prefix}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(wheel) as zf:
            zf.extractall(root)

        # auditwheel grafts into <package>.libs/ next to the package directory.
        libs_dirs = [d for d in root.iterdir() if d.is_dir() and d.name.endswith(".libs")]
        if len(libs_dirs) != 1:
            sys.exit(f"expected exactly one *.libs directory in {wheel.name}, found {libs_dirs}")
        libs_dir = libs_dirs[0]

        added = []
        for name, src in sorted(libs.items()):
            dest = libs_dir / name
            shutil.copy2(src, dest)
            dest.chmod(0o755)
            # Resolve siblings from the same directory rather than the build machine.
            subprocess.run(["patchelf", "--set-rpath", "$ORIGIN", str(dest)], check=True)
            added.append(dest)
            print(f"bundled {name} ({dest.stat().st_size // 1024} KiB)")

        record = next(root.glob("*.dist-info/RECORD"))
        with record.open("a") as fh:
            for path in added:
                fh.write(record_line(root, path))

        tmp_wheel = wheel.with_suffix(".whl.new")
        with zipfile.ZipFile(tmp_wheel, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(root).as_posix())
        tmp_wheel.replace(wheel)

    print(f"added {len(added)} OSPRay libraries to {wheel.name}")


if __name__ == "__main__":
    main()
