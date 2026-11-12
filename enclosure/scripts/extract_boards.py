#!/usr/bin/env python3
"""Extract mechanical XY geometry from the downloaded, pinned Eagle files."""
import csv
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "enclosure/generated"


def point(element, x, y):
    rotation = element.get("rot", "R0")
    angle = math.radians(float(rotation.split("R")[-1]))
    u = x * math.cos(angle) - y * math.sin(angle)
    v = x * math.sin(angle) + y * math.cos(angle)
    # Eagle mirrors the rotated package about the board's Y axis.
    if "M" in rotation:
        u = -u
    return [round(float(element.get("x")) + u, 5), round(float(element.get("y")) + v, 5)]


def extract(key):
    path = ROOT / f"hardware/reference/vendor/{key}/board.brd"
    board = ET.parse(path).find("./drawing/board")
    libraries = {lib.get("name"): {p.get("name"): p for p in lib.findall("./packages/package")} for lib in board.findall("./libraries/library")}
    edges = [w.attrib for w in board.findall("./plain/wire") if w.get("layer") == "20"]
    xs = [float(w[k]) for w in edges for k in ("x1", "x2")]
    ys = [float(w[k]) for w in edges for k in ("y1", "y2")]
    holes = [[float(h.get("x")), float(h.get("y")), float(h.get("drill"))] for h in board.findall("./plain/hole") if float(h.get("drill")) >= 2]
    elements = {}
    for element in board.findall("./elements/element"):
        package = libraries[element.get("library")][element.get("package")]
        if "MOUNTINGHOLE" in element.get("package"):
            for pad in package.findall("pad"):
                holes.append(point(element, float(pad.get("x")), float(pad.get("y"))) + [float(pad.get("drill"))])
        elements[element.get("name")] = {"x": float(element.get("x")), "y": float(element.get("y")), "rotation": element.get("rot", "R0"), "package": element.get("package")}
    return {"size": [round(max(xs) - min(xs), 5), round(max(ys) - min(ys), 5)], "origin": [min(xs), min(ys)], "holes": sorted(holes), "outline": edges, "elements": elements, "source": str(path.relative_to(ROOT))}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    boards = {key: extract(key) for key in ("feather", "scd30", "veml7700", "rtc")}
    (OUT / "boards.json").write_text(json.dumps(boards, indent=2) + "\n")
    scad = ["// Generated from pinned Adafruit Eagle PCB files; units mm.", "// See hardware/reference/manifest.json and ATTRIBUTION.md."]
    for key, data in boards.items():
        scad += [f"{key}_size = {json.dumps(data['size'])};", f"{key}_holes = {json.dumps(data['holes'])};"]
    feather = boards["feather"]["elements"]
    scad += ["feather_buttons = " + json.dumps([[feather[n]["x"], feather[n]["y"]] for n in ("SW1", "SW5", "SW3")]) + ";", "feather_reset = [44.45, 11.43];", "// Display glass outline from the mirrored DISP1 package.", "feather_glass = [11.291, 2.503, 31, 17.6];", "feather_active = [12.891, 3.903, 24.9, 14.8];"]
    light = boards["veml7700"]["elements"]["IC1"]
    scad.append(f"light_optic = [{light['x']}, {light['y']}];")
    (OUT / "boards.scad").write_text("\n".join(scad) + "\n")
    with (OUT / "mounting-holes.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["board", "hole", "x_mm", "y_mm", "drill_mm"])
        for key, board in boards.items():
            for i, hole in enumerate(board["holes"], 1):
                writer.writerow([key, i, *hole])
    for key, board in boards.items():
        print(key, board["size"], board["holes"])
