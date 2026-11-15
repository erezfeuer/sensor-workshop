#!/usr/bin/env python3
"""Export printable STLs and positioned scene meshes without an OpenGL context."""
import concurrent.futures
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "enclosure"
PRINT_PARTS = ("shell", "carrier", "feather_frame", "coupon")
SCENE_PARTS = ("shell", "carrier", "feather_frame", "feather", "scd30", "rtc", "light", "battery")
PRODUCTION_FILES = {
    "shell": "01-shell.stl",
    "carrier": "02-sensor-carrier.stl",
    "feather_frame": "03-feather-frame.stl",
}


def update_production_stls():
    """Copy the three separate, print-oriented parts into the handoff folder."""
    folder = ROOT / "production-stls"
    folder.mkdir(exist_ok=True)
    for name, filename in PRODUCTION_FILES.items():
        shutil.copyfile(CAD / "stl" / (name + ".stl"), folder / filename)
        print("PRODUCTION " + filename, flush=True)


def export(job):
    name, scene = job
    folder = CAD / ("generated/scene" if scene else "stl")
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / (name + ".stl")
    cmd = ["openscad", "--export-format", "binstl", "-o", str(dest), "-D", f'part="{name}"', "-D", "assembly_coordinates=" + str(scene).lower(), str(CAD / "sensor-workshop.scad")]
    result = subprocess.run(cmd, capture_output=True, text=True)
    log = result.stdout + result.stderr
    (folder / (name + ".log")).write_text(log)
    if result.returncode or "WARNING:" in log or "ERROR:" in log:
        raise RuntimeError(f"{name}: {log}")
    print(("SCENE " if scene else "PRINT ") + name, flush=True)


if __name__ == "__main__":
    jobs = [(name, False) for name in PRINT_PARTS] + [(name, True) for name in SCENE_PARTS]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(export, jobs):
            pass
    update_production_stls()
