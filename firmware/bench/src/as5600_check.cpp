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
// Bench bring-up step 4 of five -- docs/build/03-electrical.md 3.5.3 -- and
// the same sketch satisfies "verify the angle sensor first, in isolation" in
// docs/build/04-firmware.md 4.3, Stage 0.
//
// IT DOES TWO JOBS AND THE SECOND ONE IS THE SAFETY ONE
// ------------------------------------------------------
// 1. AGC. Sets the air gap. Read it at the working gap, shim until it sits
//    mid-scale, and WRITE THE GAP DOWN -- it is the number the other two
//    vehicles get built to.
//
// 2. Wrap. The AS5600 is single-turn absolute. Turn the sensed shaft through
//    its FULL mechanical travel and the reading must be monotonic with no
//    discontinuity. A wrap is FMEA row 2, severity 5: a garbage angle feeding
//    a position loop that drives a motor. If it wraps you mounted it on the
//    wrong shaft -- move it load-side. Do not proceed.
//
// THE AGC SCALE DEPENDS ON THE SUPPLY, AND THIS BOARD IS 3.3 V
// -------------------------------------------------------------
// The datasheet's AGC is 0..255 at 5 V but 0..128 at 3.3 V. The Teensy 4.1 is
// a 3.3 V part, so mid-scale here is about 64 and NOT 128. Aiming at 128 on a
// 3.3 V rail means closing the gap until the magnet is nearly touching and
// still reading "too weak".

#include <Arduino.h>
#include <Wire.h>

namespace {

constexpr uint8_t kAS5600 = 0x36;

constexpr uint8_t kRegStatus = 0x0B;  // MD / ML / MH
constexpr uint8_t kRegRawHi = 0x0C;   // RAW_ANGLE, unfiltered, unscaled
constexpr uint8_t kRegAgc = 0x1A;

constexpr uint8_t kStatusMD = 0x20;  // magnet detected
constexpr uint8_t kStatusML = 0x10;  // magnet too weak  -> gap too large
constexpr uint8_t kStatusMH = 0x08;  // magnet too strong -> gap too small

// 3.3 V part: AGC spans 0..128. Keep a wide working window -- the aim is to be
// clear of both rails, not to hit a number.
constexpr uint8_t kAgcLo = 40;
constexpr uint8_t kAgcHi = 90;
constexpr uint8_t kAgcMid = 64;

constexpr int32_t kCounts = 4096;      // 12-bit
constexpr int32_t kWrapJump = 2048;    // half a turn between samples = a wrap

bool ReadReg(uint8_t reg, uint8_t *out) {
  Wire.beginTransmission(kAS5600);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(kAS5600, (uint8_t)1) != 1) return false;
  *out = (uint8_t)Wire.read();
  return true;
}

bool ReadRaw(int32_t *out) {
  Wire.beginTransmission(kAS5600);
  Wire.write(kRegRawHi);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(kAS5600, (uint8_t)2) != 2) return false;
  const uint8_t hi = (uint8_t)Wire.read();
  const uint8_t lo = (uint8_t)Wire.read();
  *out = ((int32_t)(hi & 0x0F) << 8) | lo;
  return true;
}

int32_t g_prev = -1;      // -1 = no trustworthy previous sample
int32_t g_min = kCounts;
int32_t g_max = -1;
bool g_wrapped = false;
uint32_t g_last_print = 0;

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 4000) {
  }

  Wire.begin();
  Wire.setClock(100000);

  Serial.println();
  Serial.println(F("MRider bench step 4 -- AS5600 gap and wrap"));
  Serial.println(F("Turn the SENSED SHAFT by hand through its full travel,"));
  Serial.println(F("lock to lock, slowly. Watch the two verdicts below."));
  Serial.printf("AGC target on a 3.3 V board: %u..%u, aim %u.\n", kAgcLo, kAgcHi, kAgcMid);
  Serial.println();
}

void loop() {
  // WRAP DETECTION ONLY RUNS ON TRUSTWORTHY SAMPLES, and that needs the
  // STATUS register, so status is read first now. Two ways a false wrap got
  // latched in the first version of this sketch, and g_wrapped never clears:
  //
  //   1. RAW_ANGLE still returns a number with no magnet present. It is
  //      noise, it jumps, and a jump is a "wrap".
  //   2. After a failed read the previous sample is stale. If the shaft moved
  //      during the dropout, the next good sample differs by an arbitrary
  //      amount through no fault of the mounting.
  //
  // A false wrap here is not a cosmetic bug. It tells the builder to stop and
  // remount the sensor on a different shaft - FMEA row 2 - so a check that
  // cries wolf is a check that gets ignored on the day it is right.
  uint8_t agc = 0, status = 0;
  if (!ReadReg(kRegStatus, &status) || !ReadReg(kRegAgc, &agc)) {
    Serial.println(F("FAIL  no answer from 0x36. Run i2c_scan first."));
    g_prev = -1;                      // continuity is broken; do not bridge it
    delay(1000);
    return;
  }

  const bool magnet_ok = (status & kStatusMD) && !(status & kStatusML) &&
                         !(status & kStatusMH);

  // Sample fast so a quick hand movement cannot skip half a turn between
  // samples and be mistaken for a wrap.
  int32_t raw = 0;
  if (!ReadRaw(&raw)) {
    Serial.println(F("FAIL  RAW_ANGLE read failed."));
    g_prev = -1;
    delay(1000);
    return;
  }

  if (!magnet_ok) {
    g_prev = -1;                      // the angle means nothing right now
  } else {
    if (g_prev >= 0 && labs(raw - g_prev) > kWrapJump) g_wrapped = true;
    g_prev = raw;
    if (raw < g_min) g_min = raw;
    if (raw > g_max) g_max = raw;
  }

  // Unsigned elapsed-time difference, which is correct across the ~49-day
  // millis() rollover. The first version compared millis() < deadline; once
  // the deadline wrapped to a small value the large millis() was never below
  // it, so the gate opened every loop for the few milliseconds until millis()
  // wrapped too - a burst of output, not the stall it looks like.
  if ((uint32_t)(millis() - g_last_print) < 250u) {
    delay(2);
    return;
  }
  g_last_print = millis();

  const float deg = (float)raw * 360.0f / (float)kCounts;
  const int32_t span = (g_max >= 0) ? (g_max - g_min) : 0;

  Serial.printf("raw %4ld  %6.2f deg   AGC %3u   span %4ld (%5.1f deg)   ",
                (long)raw, (double)deg, agc, (long)span,
                (double)((float)span * 360.0f / (float)kCounts));

  if (!(status & kStatusMD)) {
    Serial.print(F("NO MAGNET  "));
  } else if (status & kStatusML) {
    Serial.print(F("TOO WEAK (close the gap)  "));
  } else if (status & kStatusMH) {
    Serial.print(F("TOO STRONG (open the gap)  "));
  } else if (agc < kAgcLo) {
    Serial.print(F("gap a touch small  "));
  } else if (agc > kAgcHi) {
    Serial.print(F("gap a touch large  "));
  } else {
    Serial.print(F("GAP OK  "));
  }

  Serial.println(g_wrapped ? F("** WRAPPED -- STOP, see FMEA row 2 **")
                           : (magnet_ok ? F("no wrap so far")
                                        : F("angle not trusted - not judging")));
}
