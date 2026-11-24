#!/usr/bin/env python3
"""Download pinned vendor references. Existing manifest entries are immutable."""
import concurrent.futures
from datetime import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "hardware/reference"
MANIFEST = REF / "manifest.json"


def get(url):
    req = Request(url, headers={"User-Agent": "sensor-workshop-cad/0.1"})
    with urlopen(req, timeout=60) as response:
        return response.read()


def initial_manifest():
    entries = []
    boards = {
        "feather": ("Adafruit-ESP32-S3-Reverse-TFT-Feather-PCB", "Adafruit ESP32-S3 Reverse TFT Feather"),
        "scd30": ("Adafruit-SCD-30-PCB", "Adafruit SCD30"),
        "veml7700": ("Adafruit-VEML7700-PCB", "Adafruit VEML7700 STEMMA QT"),
        "tsl2591": ("Adafruit-TSL2591-Breakout-PCB", "Adafruit TSL2591"),
        "rtc": ("Adafruit-DS3231-Precision-RTC-Breakout-PCB", "Adafruit DS3231 STEMMA QT"),
    }
    for key, (repo, stem) in boards.items():
        commit = json.loads(get(f"https://api.github.com/repos/adafruit/{repo}/commits/HEAD"))["sha"]
        for upstream, local in [(stem + ".brd", "board.brd"), (stem + ".sch", "schematic.sch"), ("license.txt", "license.txt"), ("README.md", "README.md")]:
            entries.append({"path": f"vendor/{key}/{local}", "url": f"https://raw.githubusercontent.com/adafruit/{repo}/{commit}/{quote(upstream)}", "upstream_commit": commit, "purpose": f"{key} official PCB and attribution"})
    pdfs = {
        "scd30-datasheet.pdf": "https://sensirion.com/media/documents/4EAF6AF8/61652C3C/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf",
        "scd30-design-in.pdf": "https://sensirion.com/media/documents/84D49268/616536CB/Sensirion_CO2_Sensors_SCD30_Design-In_Guidelines_D1.pdf",
        "scd30-interface.pdf": "https://sensirion.com/media/documents/D7CEEF4A/6165372F/Sensirion_CO2_Sensors_SCD30_Interface_Description.pdf",
        "veml7700-datasheet.pdf": "https://www.vishay.com/docs/84286/veml7700.pdf",
        "tsl2591-datasheet.pdf": "https://cdn-learn.adafruit.com/assets/assets/000/078/658/original/TSL2591_DS000338_6-00.pdf",
        "ds3231-datasheet.pdf": "https://cdn-shop.adafruit.com/product-files/3081/DS3231.pdf",
        "esp32-s3-datasheet.pdf": "https://cdn-learn.adafruit.com/assets/assets/000/119/042/original/esp32-s3_datasheet_en.pdf",
        "18650-reference-pack.pdf": "https://cdn-shop.adafruit.com/product-files/1781/C2253_-_ICR18650_2200mAh_3.7V_with_PCM_20140728_APPROVED_8.18.pdf",
    }
    for name, url in pdfs.items():
        entries.append({"path": "vendor/datasheets/" + name, "url": url, "purpose": "manufacturer reference"})
    entries.append({"path": "vendor/datasheets/switch-3064-product.html", "url": "https://www.adafruit.com/product/3064", "purpose": "Manufacturer switch specification; body dimensions not published"})
    for slug, name in [("esp32-s3-reverse-tft-feather", "feather"), ("adafruit-scd30", "scd30"), ("adafruit-veml7700", "veml7700"), ("adafruit-tsl2591", "tsl2591"), ("adafruit-ds3231-precision-rtc-breakout", "rtc")]:
        entries.append({"path": f"vendor/datasheets/{name}-guide.pdf", "url": f"https://cdn-learn.adafruit.com/downloads/pdf/{slug}.pdf", "purpose": "Adafruit board guide"})
    return entries


def download(entry):
    dest = REF / entry["path"]
    if dest.exists() and entry.get("sha256") == hashlib.sha256(dest.read_bytes()).hexdigest():
        return entry
    data = get(entry["url"])
    if dest.suffix == ".pdf" and not data.startswith(b"%PDF"):
        raise ValueError(f"Not a PDF: {entry['url']}")
    if dest.suffix in (".brd", ".sch") and b"<eagle" not in data:
        raise ValueError(f"Not Eagle XML: {entry['url']}")
    digest = hashlib.sha256(data).hexdigest()
    if entry.get("sha256") and entry["sha256"] != digest:
        raise ValueError(f"Upstream file changed: {entry['path']}; review before updating manifest")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {**entry, "sha256": digest, "bytes": len(data), "retrieved_date": entry.get("retrieved_date", datetime.now(ZoneInfo("Asia/Jerusalem")).date().isoformat())}


if __name__ == "__main__":
    REF.mkdir(parents=True, exist_ok=True)
    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else initial_manifest()
    results, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(download, e): e for e in entries}
        for future in concurrent.futures.as_completed(futures):
            entry = futures[future]
            try:
                results.append(future.result())
                print("OK", entry["path"], flush=True)
            except Exception as error:
                results.append(entry)
                failures.append((entry["path"], str(error)))
                print("FAILED", entry["path"], str(error), flush=True)
    MANIFEST.write_text(json.dumps(sorted(results, key=lambda e: e["path"]), indent=2) + "\n")
    if failures:
        raise SystemExit(f"{len(failures)} downloads require attention")
