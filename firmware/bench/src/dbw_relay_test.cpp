// dbw_relay_test.cpp
// DBW 릴레이와 FlySky 경로를 시험하는 임시 스케치입니다. mrider 정식 펌웨어가 아닙니다.
// 바퀴를 띄운 상태에서만 쓰세요.
//
// 하는 일
//  - 2번(조향), 3번(구동) 핀으로 1.5 ms 정지 펄스를 계속 냅니다.
//    그래서 CH5가 Teensy 쪽으로 넘어가도 MDDS30은 정지 명령을 받습니다.
//  - 시리얼 모니터에서 'd'를 보내면 GATE(21번)를 켜서 K1–K4를 DBW로 붙입니다.
//    's'를 보내면 GATE를 끄고 STOCK으로 돌아갑니다.
//  - SENSE(20번)가 낮아지면(E-stop 눌림, 코일 전원 끊김) 바로 GATE를 끄고,
//    다시 'd'를 보내기 전까지 STOCK에 머뭅니다. 저절로 DBW로 돌아가지 않습니다.
//  - DBW는 최대 120초입니다. 넘으면 저절로 STOCK으로 돌아갑니다.

#include <Arduino.h>
#include <Servo.h>

constexpr int PIN_PWM_STEER = 2;    // 신호 MUX M1 -> MDDS30 RC1 (조향)
constexpr int PIN_PWM_DRIVE = 3;    // 신호 MUX M2 -> MDDS30 RC2 (구동)
constexpr int PIN_SENSE     = 20;   // A6. 릴레이 보드 분압기, 2.56–3.11 V = 살아 있음
constexpr int PIN_GATE      = 21;   // HIGH = K1–K4 코일 켜짐 (DBW)

constexpr int      NEUTRAL_US  = 1500;
constexpr float    SENSE_ON_V  = 2.2f;     // 이 값보다 높으면 E-stop 회로가 살아 있음
constexpr float    SENSE_OFF_V = 1.5f;     // 이 값보다 낮으면 끊김
constexpr uint32_t DBW_MAX_MS  = 120000;   // DBW 최대 유지 시간

Servo steer, drive;
bool senseLive = false;
bool dbw = false;
uint32_t dbwSince = 0;
uint32_t lastPrint = 0;

float readSenseV() {
  return analogRead(PIN_SENSE) * 3.3f / 1023.0f;
}

void setGate(bool on, const char *why) {
  digitalWrite(PIN_GATE, on ? HIGH : LOW);
  digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
  if (on != dbw) {
    Serial.printf("[%s] %s\n", on ? "DBW" : "STOCK", why);
  }
  dbw = on;
  if (on) dbwSince = millis();
}

void setup() {
  pinMode(PIN_GATE, OUTPUT);
  digitalWrite(PIN_GATE, LOW);            // 시작은 언제나 STOCK
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  steer.attach(PIN_PWM_STEER);
  drive.attach(PIN_PWM_DRIVE);
  steer.writeMicroseconds(NEUTRAL_US);
  drive.writeMicroseconds(NEUTRAL_US);

  analogReadResolution(10);
  Serial.begin(115200);
  Serial.println("dbw_relay_test: STOCK으로 시작합니다. 'd' = DBW, 's' = STOCK");
}

void loop() {
  const float v = readSenseV();
  if (senseLive && v < SENSE_OFF_V) senseLive = false;
  else if (!senseLive && v > SENSE_ON_V) senseLive = true;

  if (dbw && !senseLive) {
    setGate(false, "SENSE 낮음: E-stop 눌림 또는 코일 전원 끊김. 다시 'd'를 보내야 DBW");
  }
  if (dbw && millis() - dbwSince > DBW_MAX_MS) {
    setGate(false, "120초가 지나 STOCK으로 돌아감");
  }

  while (Serial.available()) {
    const char c = Serial.read();
    if (c == 'd') {
      if (senseLive) setGate(true, "릴레이 네 개가 딸깍 붙어야 합니다");
      else Serial.println("거부: SENSE가 낮습니다. E-stop을 풀고 다시 보내세요");
    } else if (c == 's') {
      setGate(false, "사용자 요청");
    }
  }

  if (millis() - lastPrint > 1000) {
    lastPrint = millis();
    Serial.printf("SENSE %.2f V (%s) | %s\n", v, senseLive ? "살아 있음" : "끊김",
                  dbw ? "DBW" : "STOCK");
  }
}
