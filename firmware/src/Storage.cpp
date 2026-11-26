#include "Storage.h"
#include <esp_partition.h>
#include <unistd.h>
using namespace logger;
bool Storage::blankPartition() {
  auto *part = esp_partition_find_first(ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_SPIFFS,
                                        "spiffs");
  if (!part)
    return false;
  uint8_t buffer[512];
  for (size_t at = 0; at < part->size; at += sizeof(buffer)) {
    if (esp_partition_read(part, at, buffer, sizeof(buffer)) != ESP_OK)
      return false;
    for (uint8_t b : buffer)
      if (b != 0xff)
        return false;
    yield();
  }
  return true;
}
bool Storage::truncateTo(uint32_t bytes) {
  if (::truncate("/littlefs/records.bin", bytes) != 0) {
    error = "Log recovery failed. Download raw data before erasing.";
    return false;
  }
  return true;
}
bool Storage::begin(bool fast, uint32_t expected, uint32_t last) {
  mounted = LittleFS.begin(false, "/littlefs", 6, "spiffs");
  if (!mounted && blankPartition()) {
    if (LittleFS.format())
      mounted = LittleFS.begin(false, "/littlefs", 6, "spiffs");
  }
  if (!mounted) {
    error = "Storage could not mount. Existing data was not erased.";
    return false;
  }
  if (!LittleFS.exists("/records.bin")) {
    File f = LittleFS.open("/records.bin", FILE_WRITE);
    if (!f) {
      error = "Cannot create log.";
      return false;
    }
    f.close();
  }
  File f = open();
  uint32_t size = f.size();
  if (fast && size == expected && size % sizeof(Record) == 0) {
    Record r;
    if (!size || (f.seek(size - sizeof(r)) &&
                  f.read(reinterpret_cast<uint8_t *>(&r), sizeof(r)) == sizeof(r) && valid(r) &&
                  r.sequence == last)) {
      count = size / sizeof(Record);
      sequence = last;
      healthy = true;
      full = freeBytes() < StorageReserve + sizeof(Record);
      return true;
    }
  }
  f.close();
  healthy = scan();
  full = freeBytes() < StorageReserve + sizeof(Record);
  return healthy;
}
bool Storage::scan() {
  File f = open();
  uint32_t size = f.size(), good = 0, last = 0;
  Record r;
  while (good + sizeof(r) <= size) {
    if (f.read(reinterpret_cast<uint8_t *>(&r), sizeof(r)) != sizeof(r)) {
      error = "Log read failed.";
      return false;
    }
    RecordCheck decision = checkRecord(r, last, good, size);
    if (decision != RecordCheck::Good) {
      if (decision == RecordCheck::Corrupt) {
        error = "Log corruption detected. Download raw data; writing is stopped.";
        return false;
      }
      break;
    }
    last = r.sequence;
    good += sizeof(r);
    yield();
  }
  f.close();
  if (good != size) {
    recoveredBytes = size - good;
    if (!truncateTo(good))
      return false;
  }
  count = good / sizeof(Record);
  sequence = last;
  return true;
}
bool Storage::append(Record &r) {
  if (!healthy)
    return false;
  if (freeBytes() < StorageReserve + sizeof(r)) {
    full = true;
    error = "Storage full. Download and erase to continue.";
    return false;
  }
  r.sequence = sequence + 1;
  seal(r);
  File f = LittleFS.open("/records.bin", FILE_APPEND);
  if (!f) {
    healthy = false;
    error = "Cannot open log for writing.";
    return false;
  }
  size_t n = f.write(reinterpret_cast<const uint8_t *>(&r), sizeof(r));
  f.flush();
  f.close();
  if (n != sizeof(r)) {
    healthy = false;
    error = "Incomplete write. Logging stopped; saved data retained.";
    return false;
  }
  sequence = r.sequence;
  count++;
  return true;
}
bool Storage::erase() {
  // Invoked only by the explicit ERASE confirmation in the dashboard.
  if (!mounted) {
    if (!LittleFS.format()) {
      error = "Format failed.";
      return false;
    }
    mounted = LittleFS.begin(false, "/littlefs", 6, "spiffs");
    if (!mounted)
      return false;
  }
  if (LittleFS.exists("/records.bin") && !LittleFS.remove("/records.bin")) {
    error = "Erase failed.";
    return false;
  }
  File f = LittleFS.open("/records.bin", FILE_WRITE);
  if (!f)
    return false;
  f.close();
  count = 0;
  sequence = 0;
  full = false;
  healthy = true;
  error = "";
  return true;
}
