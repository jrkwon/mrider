// Copyright 2026 Jaerock Kwon
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Bench bring-up step 3 of five -- docs/build/03-electrical.md 3.5.3.
//
// WHAT THIS PROVES, AND WHY IT IS A WHOLE STEP OF ITS OWN
// -------------------------------------------------------
// That the AS5600 answers on the bus AT ALL, before any code tries to read an
// angle out of it. An angle that comes back as zero has two causes that look
// identical from a serial monitor -- a sensor that is wired wrong, and a
// sensor that is wired right and reading zero. This separates them.
//
// The design is ONE device per bus. So the pass condition is not "0x36 is
// present", it is "0x36 is present AND nothing else is". A second address
// means a second pull-up pair somewhere, or a breakout left on the rail from
// a previous bench session, and either will bite later at an awkward moment.
//
// PINS ARE NOT A CHOICE HERE
// --------------------------
// SDA = 18, SCL = 19. Fixed by the Teensy 4.1's Wire peripheral, which is why
// those two rows of the pin table in docs/build/04-firmware.md say "fixed by
// hardware" rather than "chosen".

#include <Arduino.h>
#include <Wire.h>

namespace {

constexpr uint8_t kAS5600 = 0x36;  // the only device this bus should carry

// 100 kHz, not 400. A bench rig is a metre of unshielded hookup wire next to a
// motor; standard mode has the noise margin and nothing here needs the speed.
constexpr uint32_t kBusHz = 100000;

constexpr uint8_t kFirstAddr = 0x08;  // 0x00-0x07 are reserved
constexpr uint8_t kLastAddr = 0x77;   // 0x78-0x7F are reserved

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 4000) {
  }

  Wire.begin();
  Wire.setClock(kBusHz);

  Serial.println();
  Serial.println(F("MRider bench step 3 -- I2C scan"));
  Serial.println(F("SDA = pin 18, SCL = pin 19 (fixed by hardware)"));
  Serial.println(F("Expect exactly one device: 0x36, the AS5600."));
  Serial.println();
}

void loop() {
  uint8_t found = 0;
  uint8_t last = 0;

  Serial.println(F("--- scan ---"));
  for (uint8_t addr = kFirstAddr; addr <= kLastAddr; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  device at 0x%02X\n", addr);
      found++;
      last = addr;
    }
  }

  if (found == 0) {
    Serial.println(F("FAIL  nothing answered."));
    Serial.println(F("      The bus idles HIGH through its pull-ups. Meter SDA"));
    Serial.println(F("      and SCL against GND with the sensor unplugged: both"));
    Serial.println(F("      must read 3.3 V. If they read 0 V the pull-ups are"));
    Serial.println(F("      missing or the rail is not there, and no sensor"));
    Serial.println(F("      fault is involved."));
  } else if (found == 1 && last == kAS5600) {
    Serial.println(F("PASS  0x36 alone. Go to step 4 (as5600_check)."));
  } else if (found == 1) {
    Serial.printf("FAIL  one device, but it is 0x%02X and not 0x36.\n", last);
    Serial.println(F("      This is not an AS5600. Check what is on the cable."));
  } else {
    Serial.printf("FAIL  %u devices. The design is ONE per bus.\n", found);
    Serial.println(F("      A second address means a second breakout still on"));
    Serial.println(F("      the rail, or a second pull-up pair fighting the"));
    Serial.println(F("      first. Find it now, not during a steering test."));
  }

  Serial.println();
  delay(2000);
}
