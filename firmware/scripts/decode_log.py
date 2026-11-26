#!/usr/bin/env python3
"""Convert a downloaded SLW1 raw log to CSV without modifying the input.

Stops at the first invalid record; never guesses past corruption.
"""
import argparse
import csv
import datetime as dt
from pathlib import Path
import math
import struct
import sys
import zlib
RECORD = struct.Struct('<IIIIIHHffffffHHHHII')
MAGIC = 0x31574c53
EVENTS = ['sample','clock_set','settings','start','pause','calibration','boot']
HEADER = ['sequence','event','session_id','timestamp_utc','uptime_s','settings_revision','channel_mask','quality_flags','co2_ppm','temperature_c','humidity_pct','illuminance_lux','battery_v','battery_pct','co2_age_bound_s','event_value']

def decode(data):
    previous = 0
    for at in range(0,len(data),RECORD.size):
        raw = data[at:at+RECORD.size]
        if len(raw)!=RECORD.size:
            raise ValueError(f'Torn tail at byte {at}: {len(raw)} of 64 bytes')
        r=RECORD.unpack(raw)
        if r[0]!=MAGIC or zlib.crc32(raw[:60])!=r[-1] or r[1]<=previous:
            raise ValueError(f'Invalid record at byte {at}; prefix only was recovered')
        previous=r[1]
        event=r[15]
        stamp=dt.datetime.fromtimestamp(r[3],dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if r[6]&1 else ''
        values=[f'{v:.3f}' if math.isfinite(v) and event==0 else '' for v in r[7:13]]
        yield [r[1],EVENTS[event] if event<len(EVENTS) else 'unknown',r[2],stamp,r[4],r[14],r[5],r[6],*values,r[13] if r[13]!=65535 else '',r[17]]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():parser.error('Input and output must differ')
    if args.output.exists():parser.error('Output already exists; choose a new filename')
    with args.output.open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(HEADER)
        try:
            for row in decode(args.input.read_bytes()):writer.writerow(row)
        except ValueError as error:
            print(str(error)+f'. Valid prefix saved to {args.output}',file=sys.stderr);return 2
    return 0
if __name__=='__main__':sys.exit(main())
