#!/usr/bin/env python3
"""Export printable STLs and positioned scene meshes without an OpenGL context."""
import concurrent.futures
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "enclosure"
PRINT_PARTS = ("base", "lid", "pod", "shade", "foot_front", "foot_rear", "button", "coupon")
SCENE_PARTS = ("base", "lid", "pod", "shade", "feet", "buttons", "feather", "scd30", "rtc", "light", "battery", "switch", "wires")


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
