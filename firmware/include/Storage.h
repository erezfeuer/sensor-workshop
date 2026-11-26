#pragma once
#include <Arduino.h>
#include <FS.h>
#include <LittleFS.h>
#include <LoggerCore.h>
class Storage {
public:
  bool mounted = false, healthy = false, full = false;
  uint32_t count = 0, sequence = 0, recoveredBytes = 0;
  String error;
  bool begin(bool fast, uint32_t expectedBytes, uint32_t expectedSequence);
  bool append(logger::Record &record);
  bool erase();
  File open() {
    return mounted ? LittleFS.open("/records.bin", FILE_READ) : File();
  }
  uint32_t freeBytes() const {
    return mounted ? LittleFS.totalBytes() - LittleFS.usedBytes() : 0;
  }
  uint32_t totalBytes() const {
    return mounted ? LittleFS.totalBytes() : 0;
  }

private:
  bool scan();
  bool truncateTo(uint32_t bytes);
  bool blankPartition();
};
