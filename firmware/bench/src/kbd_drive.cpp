// kbd_drive.cpp
// 키보드(시리얼 모니터)로 MDDS30을 움직이는 벤치 스케치입니다. mrider 정식 펌웨어가 아닙니다.
// 바퀴를 띄운 상태에서만 쓰세요. 빌드만 확인했고 하드웨어에서는 아직 돌려 보지 않았습니다.
// i-BUS 파서와 키 배치는 ~/mrider_serial_bench_steer100 의 것을 그대로 가져왔습니다.
//
// 누가 MDDS30을 움직이나: 두 단계로 정해집니다
// ------------------------------------------------
// 1. 하드웨어 (코드 없음). 신호 MUX(Pololu #2806)가 수신기 CH5 펄스를 직접 잽니다.
//      CH5 > 약 1.7 ms  (FS-i6 스위치 아래 = 2000 us)  -> SLAVE : 수신기 CH1/CH2 -> RC1/RC2
//      CH5 < 약 1.7 ms  (스위치 위 = 1000 us) 또는 무신호 -> MASTER: Teensy 2/3번 -> RC1/RC2
//    Teensy는 이 선택을 바꿀 수 없습니다. 펌웨어가 멈춰도 CH5만 내리면 FlySky가 잡습니다(Layer B).
//
// 2. 소프트웨어 (이 스케치). MASTER일 때 Teensy가 2/3번 핀에 무엇을 낼지 정합니다.
//    i-BUS로 CH5를 함께 읽어 지금 MUX가 어느 쪽인지 알고, 아래가 모두 맞을 때만 키보드 명령을
//    내보냅니다. 하나라도 어긋나면 정확히 1.5 ms(정지)입니다.
//      - arm 되어 있음 ('r')
//      - E-stop SENSE가 살아 있고, 살아난 지 1초가 지남 (MDDS30이 부팅하며 중립을 잡는 시간)
//      - i-BUS 프레임이 100 ms 안에 들어옴 (FlySky가 살아 있어야 CH5로 뺏을 수 있음)
//      - CH5가 MASTER(Teensy) 쪽
//      - 300 ms 안에 들어온 키 입력이 있음
//
// 상태 (docs/design/dbw.md 10.3과의 대응)
//   ESTOP : 1.5 ms만 냅니다. 부팅 직후, E-stop(SENSE 낮음), i-BUS 끊김, CH5를 FlySky로 내림,
//           USB 끊김, 스페이스. 빠져나오는 길은 'r' 하나입니다. 문서의 "E-stop 해제 + RC arm"을
//           벤치용으로 "키보드 arm + RC 조건(프레임 수신, CH5 위, 스틱 중앙)"으로 바꾼 것입니다.
//   KEY   : 키보드 명령을 냅니다. 나중에 micro-ROS DbwCommand(AUTONOMOUS)가 이 자리에 들어갑니다.
//   MANUAL_RC(i-BUS 스틱을 Teensy가 받아 각도 루프로 따라가는 모드)는 조향 루프가 생긴 뒤의 일입니다.
//   루프 없이 스틱 값을 그대로 넘기면 CH5를 내린 FlySky 직결과 다를 것이 없습니다.
//
// 릴레이 K1–K4 (GATE 21번)는 arm과 따로입니다. 'o' = DBW(MDDS30이 모터에), 'f' = STOCK.
// FlySky 직결(SLAVE)도 릴레이가 DBW여야 모터에 닿으므로 ESTOP이 릴레이를 내리지는 않습니다.
// 릴레이를 내리는 것은 'f', SENSE 낮음, USB 끊김이고, 다시 올리는 것은 'o'뿐입니다.
//
// 키 (대소문자 무관, 'H'만 대문자)
//   q w e    전진-좌 / 전진 / 전진-우     한 번 누르면 두 축을 300 ms 동안 정하고 정지로 돌아갑니다.
//   a x d    좌 / 정지 / 우               누르고 있으면 키 반복으로 이어집니다.
//   z s c    후진-좌 / 후진 / 후진-우
//   r        arm                          스페이스  disarm (ESTOP)
//   o / f    릴레이 DBW / STOCK
//   [ / ]    조향 세기 -/+ 10 us          - / =     구동 세기 -/+ 10 us
//   v        엔코더 보기 켜기/끄기         0         엔코더 카운트를 0으로
//   !        워치독 켜기 (리셋 전까지 못 끔) H        워치독 시험 ('!' 뒤에만. 일부러 멈춤 -> 약 1초 뒤 리셋)
//   ?        도움말
//
// 워치독은 부팅 때 켜지 않습니다 (2026-11-29). 부팅 때 켜는 판에서 Teensy가 1.3초마다
// 재부팅했습니다 (USB 준비 0.3초 + 타임아웃 1.0초). 먹이 주기가 안 먹히는지, 켠 직후 다른 곳에서
// 멈추는지 아직 가리지 못해서, 키로 켜서 시험할 수 있게 바꿨습니다. 모니터를 열면 직전 크래시
// 정보(CrashReport)가 있으면 찍습니다. 정식 펌웨어에서는 문서대로 부팅 때 켜야 합니다.
//
// 'd'가 실제로 오른쪽인지, 'w'가 실제로 전진인지는 아직 확인되지 않았습니다.
//
// 구동 엔코더 (홀 래치 DRV5013 ×2, 0/1번 핀) 모니터
// -------------------------------------------------
// 상태줄 아래에 한 줄을 더 찍습니다: 누적 카운트, 회전 수, 속도(cnt/s, m/s), A/B 입력 레벨.
// 'v'를 누르면 0.1초마다 엔코더 줄만 찍습니다. 바퀴나 자석을 손으로 천천히 돌리며 볼 때 씁니다.
//   - A/B 레벨은 디코더가 실제로 받는 신호(ENC1 입력 모니터 레지스터)입니다. 0/1번 핀은 XBAR로
//     디코더에 물려 있어서 digitalRead로 읽지 않습니다. 래치라서 자석이 지나간 뒤에도 값이 남아야
//     합니다 (03-electrical 3.5.3의 2단계).
//   - 한쪽으로 돌리면 카운트가 오르고 반대로 돌리면 내려가야 합니다. 한쪽으로만 오르면 두 래치가
//     반 극 간격만큼 떨어져 있지 않은 것입니다. 'w'(전진)에서 오르는지가 부호 확인입니다.
//   - 36 cnt/rev와 바퀴 반지름 0.0975 m(vehicle3.yaml)는 실측 보정 전 값입니다 (06-bench-test 6.6).

#include <Arduino.h>
#include <QuadEncoder.h>
#include <Servo.h>

namespace {

// ---- 핀: docs/build/04-firmware.md 의 핀 표 ----
constexpr int PIN_PWM_STEER = 2;   // 신호 MUX M1 -> RC1 (Left = 조향)
constexpr int PIN_PWM_DRIVE = 3;   // 신호 MUX M2 -> RC2 (Right = 구동)
constexpr int PIN_SENSE     = 20;  // A6. 릴레이 보드 분압 10k/2.7k, 2.56–3.11 V = 살아 있음
constexpr int PIN_GATE      = 21;  // HIGH = K1–K4 코일 켜짐 (DBW)
// i-BUS: Serial3, RX3 = 15번. TX3는 연결하지 않습니다.

constexpr int NEUTRAL_US = 1500;

// ---- i-BUS와 신호 MUX ----
constexpr uint32_t IBUS_TIMEOUT_MS   = 100;
constexpr int SEL_MASTER_BELOW_US    = 1600;  // MUX 문턱(약 1.7 ms)에서 양쪽으로 여유를 둠.
constexpr int SEL_SLAVE_ABOVE_US     = 1800;  // 그 사이 값은 "모름"으로 보고 정지.
constexpr int STICK_CENTER_TOL_US    = 60;

// ---- E-stop SENSE ----
constexpr float    SENSE_ON_V  = 2.2f;   // 이보다 높으면 살아 있음 (문서: 2.2–3.1 V)
constexpr float    SENSE_OFF_V = 1.5f;   // 이보다 낮으면 끊김
constexpr uint32_t HOLDOFF_MS  = 1000;   // 살아난 뒤 정지 펄스만 내는 시간 (04-firmware 4.3)

// ---- 키보드 ----
constexpr uint32_t KEY_HOLD_MS = 300;
constexpr int STEP_US = 10;
constexpr int STEER_MIN_US = 20, STEER_MAX_US = 200;
constexpr int DRIVE_MIN_US = 20, DRIVE_MAX_US = 150;
constexpr uint32_t STATUS_MS = 500;
constexpr uint32_t ENC_VIEW_MS = 100;

// ---- 구동 엔코더 ----
constexpr int32_t  COUNTS_PER_REV  = 36;       // 자석 18개 -> 9주기 -> 네 모서리 = 36. 설계값
constexpr float    WHEEL_RADIUS_M  = 0.0975f;  // vehicle3.yaml, 2026-11-28 측정 (지름 195 mm)
constexpr uint32_t SPEED_WINDOW_MS = 250;      // 이 간격의 카운트 차이로 속도를 냅니다
// ENC1 입력 모니터 레지스터(IMR) 비트, i.MX RT1060 RM: 3 = PHA, 2 = PHB (필터 전 원신호)
constexpr uint16_t IMR_PHA = 1u << 3;
constexpr uint16_t IMR_PHB = 1u << 2;

// ---- 워치독 (WDOG1): 타임아웃 = (WT + 1) × 0.5 s ----
constexpr uint8_t WDOG_WT = 1;  // 1.0 s

#define SAY(...) do { if (Serial) Serial.printf(__VA_ARGS__); } while (0)

Servo steer, drive;

// i-BUS
uint8_t frame[32];
size_t used = 0;
int ch[6] = {NEUTRAL_US, NEUTRAL_US, NEUTRAL_US, NEUTRAL_US, NEUTRAL_US, NEUTRAL_US};
bool seen = false;
uint32_t lastFrameMs = 0;
uint32_t frames = 0;

// SENSE
float senseV = 0.0f;
bool senseLive = false;
uint32_t senseLiveSince = 0;

// 상태
enum class Mode : uint8_t { Estop, Key };
enum class Sel : uint8_t { Master, Slave, Unknown };
Mode mode = Mode::Estop;
bool relayDbw = false;

// 키 명령
int steerStep = 60, driveStep = 50;  // 참고 스케치와 같은 시작값
int keySteer = 0, keyDrive = 0;      // 중립에서 뺄 / 더할 us
bool keyActive = false;
uint32_t keyUntil = 0;

int outSteer = NEUTRAL_US, outDrive = NEUTRAL_US;
uint32_t lastStatusMs = 0, lastRefuseMs = 0;
bool wasSerial = false;

// 구동 엔코더: 채널 1(ENC1), A = 0번, B = 1번, 내부 풀업 없음 (신호 보드의 10k 풀업)
QuadEncoder enc(1, 0, 1, 0);
int32_t encZero = 0;        // '0'을 눌렀을 때의 원값
int32_t encCount = 0;       // encZero 기준 누적 카운트
float encCps = 0.0f;        // counts/s
int32_t speedRefCount = 0;
uint32_t speedRefMs = 0;
bool encView = false;

bool wdtArmed = false;

// ---------------------------------------------------------------- 워치독
// 센서를 읽고 출력을 쓴 루프 끝에서만 먹입니다 (docs/design/safety.md 2절).
// 서보 펄스는 IntervalTimer 인터럽트가 만들기 때문에 루프가 멈춰도 마지막 폭이 계속 나갑니다.
// 그것을 끊는 것은 워치독 리셋뿐입니다. 이 스케치에서는 '!'로 켭니다 (머리 주석 참고).
void watchdogBegin() {
  CCM_CCGR3 |= CCM_CCGR3_WDOG1(CCM_CCGR_ON);
  WDOG1_WMCR = 0;  // power-down 카운터 끔
  WDOG1_WCR = WDOG_WCR_SRS | WDOG_WCR_WDA | WDOG_WCR_WT(WDOG_WT) |
              WDOG_WCR_WDE | WDOG_WCR_WDT | WDOG_WCR_SRE;
  wdtArmed = true;
}

void watchdogFeed() {
  WDOG1_WSR = 0x5555;
  WDOG1_WSR = 0xAAAA;
}

[[noreturn]] void hangTest() {
  SAY("[HANG] 루프를 일부러 멈춥니다. 마지막 펄스 %d / %d us가 계속 나갑니다.\n", outSteer, outDrive);
  SAY("       약 1초 안에 Teensy가 리셋되고 펄스가 끊겨야 합니다. 안 되면 E-stop을 누르세요.\n");
  Serial.flush();
  for (;;) {
    __asm__ volatile("nop");
  }
}

// ---------------------------------------------------------------- 입력
// FlySky i-BUS: 0x20, 0x40, 14채널 리틀엔디언, 체크섬. 프레임이 온다고 RF가 살아 있는 것은 아닙니다.
// 수신기는 RF가 끊겨도 failsafe 값(또는 마지막 값)으로 프레임을 계속 보낼 수 있습니다.
void readIbus() {
  while (Serial3.available() > 0) {
    const uint8_t b = (uint8_t)Serial3.read();
    if (used == 0 && b != 0x20) continue;
    if (used == 1 && b != 0x40) {
      used = (b == 0x20) ? 1 : 0;
      continue;
    }
    frame[used++] = b;
    if (used != sizeof(frame)) continue;
    used = 0;
    uint16_t sum = 0xffff;
    for (size_t i = 0; i < 30; ++i) sum -= frame[i];
    const uint16_t check = (uint16_t)frame[30] | ((uint16_t)frame[31] << 8);
    if (sum != check) continue;
    int v[6];
    bool plausible = true;
    for (int i = 0; i < 6; ++i) {
      v[i] = frame[2 + 2 * i] | (frame[3 + 2 * i] << 8);
      if (v[i] < 900 || v[i] > 2100) plausible = false;
    }
    if (!plausible) continue;
    for (int i = 0; i < 6; ++i) ch[i] = v[i];
    lastFrameMs = millis();
    seen = true;
    ++frames;
  }
}

bool ibusFresh(uint32_t now) {
  return seen && (uint32_t)(now - lastFrameMs) < IBUS_TIMEOUT_MS;
}

// MUX가 지금 누구를 넘기고 있는지, CH5 값으로 추정합니다. MUX가 실제로 재는 값과 같은 펄스입니다.
Sel muxSel(uint32_t now) {
  if (!ibusFresh(now)) return Sel::Unknown;
  if (ch[4] < SEL_MASTER_BELOW_US) return Sel::Master;
  if (ch[4] > SEL_SLAVE_ABOVE_US) return Sel::Slave;
  return Sel::Unknown;
}

void updateSense(uint32_t now) {
  senseV = analogRead(PIN_SENSE) * 3.3f / 1023.0f;
  if (senseLive && senseV < SENSE_OFF_V) {
    senseLive = false;
  } else if (!senseLive && senseV > SENSE_ON_V) {
    senseLive = true;
    senseLiveSince = now;
  }
}

bool senseReady(uint32_t now) {
  return senseLive && (uint32_t)(now - senseLiveSince) >= HOLDOFF_MS;
}

void updateEncoder(uint32_t now) {
  encCount = enc.read() - encZero;
  const uint32_t dt = now - speedRefMs;
  if (dt >= SPEED_WINDOW_MS) {
    encCps = (float)(encCount - speedRefCount) * 1000.0f / (float)dt;
    speedRefCount = encCount;
    speedRefMs = now;
  }
}

void zeroEncoder(uint32_t now) {
  encZero = enc.read();
  encCount = 0;
  speedRefCount = 0;
  speedRefMs = now;
  encCps = 0.0f;
}

// ---------------------------------------------------------------- 상태 바꾸기
void enterEstop(const char *why) {
  keyActive = false;
  if (mode != Mode::Estop) SAY("[ESTOP] %s\n", why);
  mode = Mode::Estop;
}

void setRelay(bool on, const char *why) {
  keyActive = false;  // 접점이 움직일 때는 정지 펄스
  steer.writeMicroseconds(NEUTRAL_US);
  drive.writeMicroseconds(NEUTRAL_US);
  digitalWrite(PIN_GATE, on ? HIGH : LOW);
  if (on != relayDbw) SAY("[릴레이 %s] %s\n", on ? "DBW" : "STOCK", why);
  relayDbw = on;
}

void tryArm(uint32_t now) {
  const char *why = nullptr;
  if (!senseLive) {
    why = "SENSE 낮음. E-stop을 돌려 푸세요";
  } else if (!senseReady(now)) {
    why = "E-stop이 풀린 지 1초가 안 됐습니다. 이 동안의 arm은 받지 않습니다";
  } else if (!ibusFresh(now)) {
    why = "i-BUS 프레임 없음. 송신기를 켜고 15번 핀 배선을 확인하세요";
  } else if (muxSel(now) != Sel::Master) {
    why = "CH5가 Teensy(MASTER) 쪽이 아닙니다. 스위치를 위로";
  } else if (abs(ch[0] - NEUTRAL_US) > STICK_CENTER_TOL_US ||
             abs(ch[1] - NEUTRAL_US) > STICK_CENTER_TOL_US) {
    why = "CH1/CH2 스틱을 가운데에 두고 손을 떼세요";
  }
  if (why) {
    SAY("거부: %s\n", why);
    return;
  }
  mode = Mode::Key;
  keyActive = false;
  SAY("[KEY] arm. q w e / a x d / z s c 로 움직입니다. 스페이스 = 정지\n");
  if (!relayDbw) SAY("      릴레이가 STOCK이라 모터에는 닿지 않습니다. 'o' = DBW\n");
}

// 하나라도 어긋나면 정지로 떨어뜨립니다. 매 루프 돕니다.
void supervise(uint32_t now) {
  if (!Serial) {  // 시리얼 모니터가 닫힘 = 조작하는 사람이 없음
    while (Serial.available() > 0) Serial.read();
    if (relayDbw) setRelay(false, "USB 끊김");
    enterEstop("USB 끊김");
  }
  if (!senseLive) {
    if (relayDbw) setRelay(false, "SENSE 낮음: E-stop 눌림 또는 코일 전원 끊김. 다시 'o'를 보내야 DBW");
    enterEstop("SENSE 낮음 (E-stop)");
  }
  if (mode == Mode::Key) {
    if (!ibusFresh(now)) {
      enterEstop("i-BUS 프레임 끊김. 수신기 전원과 15번 배선을 보세요");
    } else if (muxSel(now) != Sel::Master) {
      enterEstop("CH5가 FlySky 쪽으로 넘어감. Teensy는 손을 뗍니다. 다시 쓰려면 CH5 위 + 'r'");
    }
  }
  if (keyActive && (int32_t)(now - keyUntil) >= 0) keyActive = false;
}

void printHelp() {
  SAY("\nkbd_drive: 키보드로 MDDS30을 움직이는 벤치 스케치. 바퀴를 띄운 상태에서만.\n");
  SAY("  CH5 아래 = FlySky 직결(하드웨어), CH5 위 = Teensy. Teensy는 arm된 동안만 키 명령을 냅니다.\n");
  SAY("  r = arm   스페이스 = 정지(ESTOP)   o / f = 릴레이 DBW / STOCK\n");
  SAY("  q w e / a x d / z s c = 이동 (300 ms)   [ ] = 조향 세기   - = = 구동 세기   ? = 도움말\n");
  SAY("  v = 엔코더 보기 켜기/끄기 (0.1초마다 엔코더 줄만)   0 = 엔코더 카운트를 0으로\n");
  SAY("  ! = 워치독 켜기 (리셋 전까지 못 끔)   H = 워치독 시험 ('!' 뒤에만. 약 1초 뒤 리셋되어야 함)\n\n");
}

void handleKeys(uint32_t now) {
  while (Serial && Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == 'H') {
      if (wdtArmed) hangTest();
      SAY("거부: 워치독이 꺼져 있습니다. 먼저 '!'. 꺼진 채로 멈추면 마지막 펄스가 계속 나갑니다\n");
      continue;
    }
    if (c == '!') {
      if (wdtArmed) {
        SAY("워치독은 이미 켜져 있습니다\n");
      } else {
        watchdogBegin();
        SAY("[워치독 켬] 1.0초. 이대로 리셋되면 먹이 주기가 안 먹히는 것입니다 (알려 주세요)\n");
      }
      continue;
    }
    if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a');

    switch (c) {
      case '\r': case '\n': continue;
      case ' ': enterEstop("스페이스: 사용자 정지"); continue;
      case 'r': tryArm(now); continue;
      case 'o':
        if (senseLive) setRelay(true, "K1–K4가 딸깍 붙어야 합니다");
        else SAY("거부: SENSE 낮음. E-stop을 풀고 다시 보내세요\n");
        continue;
      case 'f': setRelay(false, "사용자 요청"); continue;
      case '?': printHelp(); continue;
      case 'v':
        encView = !encView;
        SAY("엔코더 보기 %s\n", encView ? "켬 (0.1초마다, 'v'로 끔)" : "끔");
        continue;
      case '0':
        zeroEncoder(now);
        SAY("엔코더 카운트를 0으로\n");
        continue;
      case '[': case ']':
        steerStep = constrain(steerStep + (c == ']' ? STEP_US : -STEP_US), STEER_MIN_US, STEER_MAX_US);
        SAY("조향 세기 %d us\n", steerStep);
        continue;
      case '-': case '=':
        driveStep = constrain(driveStep + (c == '=' ? STEP_US : -STEP_US), DRIVE_MIN_US, DRIVE_MAX_US);
        SAY("구동 세기 %d us\n", driveStep);
        continue;
      default: break;
    }

    int s = 0, d = 0;
    switch (c) {
      case 'w': d = +1; break;
      case 's': d = -1; break;
      case 'a': s = -1; break;
      case 'd': s = +1; break;
      case 'q': d = +1; s = -1; break;
      case 'e': d = +1; s = +1; break;
      case 'z': d = -1; s = -1; break;
      case 'c': d = -1; s = +1; break;
      case 'x': break;
      default:
        keyActive = false;
        SAY("모르는 키 '%c': 정지\n", c);
        continue;
    }
    if (mode != Mode::Key) {
      if ((uint32_t)(now - lastRefuseMs) >= 1000) {
        lastRefuseMs = now;
        SAY("무시: arm 전입니다 ('r')\n");
      }
      continue;
    }
    keySteer = s * steerStep;
    keyDrive = d * driveStep;
    keyActive = true;
    keyUntil = now + KEY_HOLD_MS;
  }
}

// ---------------------------------------------------------------- 출력
void writeOutputs(uint32_t now) {
  int s = NEUTRAL_US, d = NEUTRAL_US;
  // 마지막 관문. supervise()와 일부러 겹칩니다: 조건 하나가 빠져도 정지 쪽으로 떨어지게.
  if (mode == Mode::Key && keyActive && senseReady(now) && ibusFresh(now) &&
      muxSel(now) == Sel::Master) {
    s = NEUTRAL_US + keySteer;
    d = NEUTRAL_US + keyDrive;
  }
  outSteer = s;
  outDrive = d;
  steer.writeMicroseconds(s);
  drive.writeMicroseconds(d);
}

void printStatus(uint32_t now) {
  const Sel sel = muxSel(now);
  SAY("%s | MUX %s | 릴레이 %s | SENSE %.2fV %s | IBUS %s CH1 %d CH2 %d CH5 %d | OUT %d/%d | 세기 %d/%d | WDT %s\n",
      mode == Mode::Key ? "KEY  " : "ESTOP",
      sel == Sel::Master ? "Teensy" : (sel == Sel::Slave ? "FlySky" : "?"),
      relayDbw ? "DBW" : "STOCK",
      senseV, senseLive ? (senseReady(now) ? "ok" : "대기") : "끊김",
      ibusFresh(now) ? "ok" : "없음", ch[0], ch[1], ch[4],
      outSteer, outDrive, steerStep, driveStep, wdtArmed ? "켬" : "끔");
}

void printEncoder() {
  const uint16_t imr = ENC1_IMR;
  const float revs = (float)encCount / (float)COUNTS_PER_REV;
  const float rps = encCps / (float)COUNTS_PER_REV;
  const float mps = rps * 2.0f * PI * WHEEL_RADIUS_M;
  SAY("  ENC  count %7ld (%+8.2f rev) | %+7.1f cnt/s  %+6.2f rev/s  %+5.2f m/s | A %d  B %d\n",
      (long)encCount, revs, encCps, rps, mps,
      (imr & IMR_PHA) ? 1 : 0, (imr & IMR_PHB) ? 1 : 0);
}

}  // namespace

void setup() {
  digitalWrite(PIN_GATE, LOW);
  pinMode(PIN_GATE, OUTPUT);           // 시작은 언제나 STOCK
  pinMode(PIN_SENSE, INPUT_PULLDOWN);  // 릴레이 보드가 없을 때 떠 있지 않게 (analogRead도 풀다운 유지)
  pinMode(LED_BUILTIN, OUTPUT);

  steer.attach(PIN_PWM_STEER);
  drive.attach(PIN_PWM_DRIVE);
  steer.writeMicroseconds(NEUTRAL_US);
  drive.writeMicroseconds(NEUTRAL_US);

  enc.setInitConfig();
  enc.init();

  analogReadResolution(10);
  Serial.begin(115200);
  Serial3.begin(115200);  // i-BUS, 8N1, 반전 없음
}

void loop() {
  const uint32_t now = millis();
  readIbus();
  updateSense(now);
  updateEncoder(now);

  const bool connected = Serial;
  if (connected && !wasSerial) {  // 모니터를 연 순간에 도움말과 직전 크래시 정보
    printHelp();
    if (CrashReport) Serial.print(CrashReport);
  }
  wasSerial = connected;

  handleKeys(now);
  supervise(now);
  writeOutputs(now);
  digitalWrite(LED_BUILTIN, relayDbw ? HIGH : LOW);

  if (wdtArmed) watchdogFeed();  // 센서를 읽고 출력을 쓴 뒤에만

  if ((uint32_t)(now - lastStatusMs) >= (encView ? ENC_VIEW_MS : STATUS_MS)) {
    lastStatusMs = now;
    if (!encView) printStatus(now);
    printEncoder();
  }
}
