#!/usr/bin/env python3
"""Build a single-file, offline demo from the production dashboard and test fixture."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / 'web/index.html').read_text()
mock = (root / 'tests/mock_device.js').read_text()
banner = ('<aside style="padding:12px 24px;background:#fff1d5;color:#725015;'
          'text-align:center;font:14px system-ui">'
          '<strong>INTERACTIVE PREVIEW — SIMULATED DATA</strong> · '
          'Nothing here connects to or changes your device. '
          'Runtime calculator assumptions are the same as the firmware.</aside>')
html = html.replace('<body>', '<body>' + banner, 1)
html = html.replace('<script>', '<script>\n' + mock + '\n</script>\n<script>', 1)
(root / 'preview.html').write_text(html)
print('Built firmware/preview.html; production firmware uses web/index.html only.')
