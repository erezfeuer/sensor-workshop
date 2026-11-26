import importlib.util
from pathlib import Path
import struct
import unittest
import zlib
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('decoder',HERE/'scripts/decode_log.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
def record(sequence=1,event=0,flags=1):
    fields=[d.MAGIC,sequence,123,1795680000,60,31,flags,421.5,25.25,55.,10.,3.8,80.,2,4,event,0,425,0]
    raw=d.RECORD.pack(*fields);return raw[:60]+struct.pack('<I',zlib.crc32(raw[:60]))
class DecoderTests(unittest.TestCase):
    def test_schema_and_units(self):
        row=list(d.decode(record()))[0]
        self.assertEqual(len(row),len(d.HEADER));self.assertEqual(row[8:14],['421.500','25.250','55.000','10.000','3.800','80.000'])
        self.assertEqual(row[5:8],[4,31,1]);self.assertTrue(row[3].endswith('Z'))
    def test_unset_clock_and_event(self):
        row=list(d.decode(record(event=5,flags=0)))[0]
        self.assertEqual(row[1],'calibration');self.assertEqual(row[3],'');self.assertEqual(row[8:14],['']*6);self.assertEqual(row[-1],425)
    def test_all_partial_tails(self):
        for n in range(1,64):
            rows=d.decode(record()+record(2)[:n]);self.assertEqual(next(rows)[0],1)
            with self.assertRaises(ValueError):next(rows)
    def test_corruption_stops_at_first_fault(self):
        for i in range(64):
            bad=bytearray(record(2));bad[i]^=1;rows=d.decode(record()+bad+record(3));self.assertEqual(next(rows)[0],1)
            with self.assertRaises(ValueError):next(rows)
    def test_sequence_cannot_go_backwards(self):
        with self.assertRaises(ValueError):list(d.decode(record()+record()))
if __name__=='__main__':unittest.main()
