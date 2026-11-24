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
    component_envelopes = []
    for element in board.findall("./elements/element"):
        package = libraries[element.get("library")][element.get("package")]
        if "MOUNTINGHOLE" in element.get("package"):
            for pad in package.findall("pad"):
                holes.append(point(element, float(pad.get("x")), float(pad.get("y"))) + [float(pad.get("drill"))])
        elements[element.get("name")] = {"x": float(element.get("x")), "y": float(element.get("y")), "rotation": element.get("rot", "R0"), "package": element.get("package")}
        if key == "tsl2591" and element.get("name") in ("C1", "C2", "C3", "U2", "Q2", "R1", "R3", "D1"):
            # Pad/body XY envelope from Eagle; 2 mm above PCB is a conservative
            # design allowance, not a measured component height. The light-well
            # relief adds 0.3 mm around this envelope.
            points = []
            for wire in package.findall("wire"):
                if wire.get("layer") == "51":
                    points += [point(element, float(wire.get("x1")), float(wire.get("y1"))),
                               point(element, float(wire.get("x2")), float(wire.get("y2")))]
            for pad in package.findall("smd"):
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        local = point(pad, sx * float(pad.get("dx")) / 2, sy * float(pad.get("dy")) / 2)
                        points.append(point(element, *local))
            lo = [min(p[i] for p in points) for i in (0, 1)]
            hi = [max(p[i] for p in points) for i in (0, 1)]
            component_envelopes.append({"name": element.get("name"), "xy_min": lo,
                "size": [round(hi[i]-lo[i], 5) for i in (0, 1)] + [2.0]})
    result = {"size": [round(max(xs) - min(xs), 5), round(max(ys) - min(ys), 5)], "origin": [min(xs), min(ys)], "holes": sorted(holes), "outline": edges, "elements": elements, "component_envelopes": component_envelopes, "source": str(path.relative_to(ROOT))}
    if key in ("tsl2591", "veml7700"):
        chip = elements["U1" if key == "tsl2591" else "IC1"]
        result["optic"] = point({"x": chip["x"], "y": chip["y"], "rot": chip["rotation"]}, 0, -.370 if key == "tsl2591" else 0)
        result["package_size"] = [2, 2.4, .65] if key == "tsl2591" else [6.8, 3, 2.35]
    return result


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    boards = {key: extract(key) for key in ("feather", "scd30", "veml7700", "rtc", "tsl2591")}
    (OUT / "boards.json").write_text(json.dumps(boards, indent=2) + "\n")
    scad = ["// Generated from pinned Adafruit Eagle PCB files; units mm.", "// See hardware/reference/manifest.json and ATTRIBUTION.md."]
    for key, data in boards.items():
        scad += [f"{key}_size = {json.dumps(data['size'])};", f"{key}_holes = {json.dumps(data['holes'])};"]
    feather = boards["feather"]["elements"]
    scad += ["feather_buttons = " + json.dumps([[feather[n]["x"], feather[n]["y"]] for n in ("SW1", "SW5", "SW3")]) + ";", "feather_reset = [44.45, 11.43];", "// Display glass outline from the mirrored DISP1 package.", "feather_glass = [11.291, 2.503, 31, 17.6];", "feather_active = [12.891, 3.903, 24.9, 14.8];"]
    for key, component in (("veml7700", "IC1"), ("tsl2591", "U1")):
        light = boards[key]["elements"][component]
        scad.append(f"{key}_package_center = [{light['x']}, {light['y']}];")
    # TSL2591 datasheet p24: array centre 0.370 mm below package centre in
    # the unrotated top view; U1 is rotated 180 degrees on this board.
    scad += [f"{key}_optic = {json.dumps(boards[key]['optic'])};" for key in ("veml7700", "tsl2591")]
    scad += [
             'light_size = light_sensor == "tsl2591" ? tsl2591_size : veml7700_size;',
             'light_holes = light_sensor == "tsl2591" ? tsl2591_holes : veml7700_holes;',
             'light_optic = light_sensor == "tsl2591" ? tsl2591_optic : veml7700_optic;',
             'light_package_center = light_sensor == "tsl2591" ? tsl2591_package_center : veml7700_package_center;',
             'light_package_size = light_sensor == "tsl2591" ? [2, 2.4, 0.65] : [6.8, 3, 2.35];',
             "tsl2591_components = " + json.dumps([[*c['xy_min'], *c['size']] for c in boards['tsl2591']['component_envelopes']]) + ";"]
    (OUT / "boards.scad").write_text("\n".join(scad) + "\n")
    with (OUT / "mounting-holes.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["board", "hole", "x_mm", "y_mm", "drill_mm"])
        for key, board in boards.items():
            for i, hole in enumerate(board["holes"], 1):
                writer.writerow([key, i, *hole])
    for key, board in boards.items():
        print(key, board["size"], board["holes"])
