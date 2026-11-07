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
// Bench bring-up step 5 of five -- docs/build/03-electrical.md 3.5.3, and the
// LAST step for a reason: everything it can tell you is cheap to learn here
// and expensive to learn on a wheel.
//
// WHAT A COUNT PROVES THAT A VOLTAGE DOES NOT
// --------------------------------------------
// Step 2 already showed each latch snapping between 0 V and 3.3 V. That says
// both sensors work. It says nothing about whether they are HALF A POLE PITCH
// APART, and that is the whole quadrature scheme. Counting up one way and
// down the other is the first proof the (n + 1/2) spacing is right.
//
// THE NUMBER TO EXPECT
// --------------------
// 18 magnets of alternating polarity is 9 electrical cycles per revolution.
// The Teensy 4.1's hardware decoder counts all four edges of each cycle, so
// one full turn of the carrier is 9 x 4 = 36 counts, which is the counts/rev
// the sizing table in docs/build/01-bom-sourcing.md settled on.
//
//   turn the carrier one full revolution  ->  +/- 36
//   turn it back                          ->  back to where it started
//
// A count that drifts after a there-and-back is a missed edge, not a rounding
// error: the decoder does not round.
//
// PINS, AND WHY THERE IS NO INTERNAL PULL-UP
// -------------------------------------------
// A = pin 0, B = pin 1, from the frozen pin table in
// docs/build/04-firmware.md. The DRV5013 output is OPEN DRAIN, so the signal
// board carries an external 10 k pull-up on each line -- which is why the
// QuadEncoder pull-up argument below is 0. If the counts never move, meter
// each line at rest before suspecting this sketch: both should sit at 3.3 V.
//
// Taking pins 0 and 1 forecloses Serial1. That is a decision already recorded
// in the pin table, not a surprise to discover here.

#include <Arduino.h>
#include <QuadEncoder.h>

namespace {

constexpr uint8_t kPinA = 0;
constexpr uint8_t kPinB = 1;
constexpr int32_t kCountsPerRev = 36;  // 18 magnets -> 9 cycles -> x4

// channel 1, phase A pin, phase B pin, 0 = no internal pull-up (external 10 k)
QuadEncoder g_enc(1, kPinA, kPinB, 0);

int32_t g_last = 0;
int32_t g_min = 0;
int32_t g_max = 0;
uint32_t g_next_print = 0;

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 4000) {
  }

  g_enc.setInitConfig();
  g_enc.init();

  Serial.println();
  Serial.println(F("MRider bench step 5 -- quadrature counts"));
  Serial.printf("A = pin %u, B = pin %u, external 10k pull-ups assumed.\n", kPinA, kPinB);
  Serial.printf("One full turn of the carrier = %ld counts.\n", (long)kCountsPerRev);
  Serial.println(F("Pass a magnet across A then B and the count rises;"));
  Serial.println(F("B then A and it falls. If it only ever rises, the two"));
  Serial.println(F("latches are not half a pole pitch apart."));
  Serial.println();
}

void loop() {
  const int32_t now = g_enc.read();

  if (now < g_min) g_min = now;
  if (now > g_max) g_max = now;

  if (millis() < g_next_print) {
    delay(2);
    return;
  }
  g_next_print = millis() + 200;

  const int32_t delta = now - g_last;
  g_last = now;

  const float revs = (float)now / (float)kCountsPerRev;
  Serial.printf("count %7ld  (%+6.2f rev)  delta %+4ld  seen %ld..%ld  %s\n",
                (long)now, (double)revs, (long)delta, (long)g_min, (long)g_max,
                delta > 0 ? "forward" : (delta < 0 ? "reverse" : "--"));
}
