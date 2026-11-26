#!/usr/bin/env python3
"""Check built binaries, the actual partition table and embedded dashboard.

Run after both PlatformIO builds; this does not access a serial port or hardware.
"""
import gzip
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
board = Path.home() / '.platformio/platforms/espressif32/boards/adafruit_feather_esp32s3_reversetft.json'
partitions = {}
for line in (ROOT / 'partitions.csv').read_text().splitlines():
    if not line.strip() or line.lstrip().startswith('#'):
        continue
    name, kind, subtype, offset, size, *_ = [part.strip() for part in line.split(',')]
    partitions[name] = (int(offset, 0), int(size, 0))
end = 0
for name, (offset, size) in sorted(partitions.items(), key=lambda entry: entry[1][0]):
    assert offset >= end, f'Overlapping partition: {name}'
    assert offset % 4096 == 0 and size % 4096 == 0
    end = offset + size
assert end == 4 * 1024 * 1024
assert partitions['spiffs'] == (0x170000, 0x160000)
assert partitions['uf2'] == (0x2d0000, 0x40000)
board_info = json.loads(board.read_text())
extras = board_info['upload']['arduino']['flash_extra_images']
assert any(int(offset, 0) == partitions['uf2'][0] and 'tinyuf2' in path for offset, path in extras)

html = (ROOT / 'web/index.html').read_bytes()
header = (ROOT / 'include/web_asset.h').read_text()
compressed = bytes(int(n) for n in re.findall(r'\d+', header.split('{', 1)[1]))
assert gzip.decompress(compressed) == html
assert b'DemoDevice' not in html and b'SIMULATED DATA' not in html
assert 'src="http' not in html.decode() and 'src=\'http' not in html.decode()
assert 'INTERACTIVE PREVIEW' in (ROOT / 'preview.html').read_text()

builds = {}
for environment in ('feather', 'feather-debug'):
    folder = ROOT / '.pio/build' / environment
    image = (folder / 'firmware.bin').read_bytes()
    assert image[0] == 0xe9 and len(image) <= partitions['app0'][1]
    entries = (folder / 'partitions.bin').read_bytes()
    found = {}
    for at in range(0, len(entries), 32):
        magic, kind, subtype, offset, size, label, flags = struct.unpack('<HBBII16sI', entries[at:at+32])
        if magic != 0x50aa:
            break
        found[label.rstrip(b'\x00').decode()] = (offset, size)
    assert found == partitions, f'Compiled partition mismatch: {environment}'
    builds[environment] = {'binary_bytes': len(image), 'sha256': hashlib.sha256(image).hexdigest()}
result = {'builds': builds, 'flash_bytes': end, 'log_partition_bytes': partitions['spiffs'][1],
          'embedded_html_bytes': len(html), 'embedded_gzip_bytes': len(compressed),
          'checks': ['Nonoverlapping 4 MB flash map', 'TinyUF2 upload address preserved',
                     'Both application images fit', 'Compiled partition tables match source',
                     'Embedded dashboard matches production HTML exactly', 'No demo fixture in firmware'],
          'hardware_accessed': False}
out = ROOT / 'tests/artifacts/build-results.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
