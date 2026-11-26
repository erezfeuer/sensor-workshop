"""Embed the offline dashboard in the application, keeping the log FS separate."""
Import('env')
import gzip
from pathlib import Path
root = Path(env.subst('$PROJECT_DIR'))
data = gzip.compress((root / 'web/index.html').read_bytes(), compresslevel=9, mtime=0)
out = root / 'include/web_asset.h'
text = '#pragma once\n#include <Arduino.h>\nstatic const uint8_t WEB_GZ[] PROGMEM = {\n'
text += ',\n'.join(','.join(str(b) for b in data[i:i+24]) for i in range(0,len(data),24))
text += '\n};\n'
if not out.exists() or out.read_text() != text:
    out.write_text(text)
print('Embedded dashboard:', len(data), 'gzip bytes')
