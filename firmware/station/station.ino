// note: the station never decides, it only executes host commands and reports arrivals
// note: line protocol at 115200 baud, documented in the README

#include <Servo.h>

#define HAS_LCD 0  // set to 1 if the parallel LCD 1602 is wired (pins A0-A5)
#if HAS_LCD
#include <LiquidCrystal.h>
LiquidCrystal lcd(A0, A1, A2, A3, A4, A5);
#endif

const byte PIN_LED_A = 2;
const byte PIN_LED_B = 3;
const byte PIN_LED_C = 4;
const byte PIN_LED_HOLD = 5;  // yellow
const byte PIN_LED_DENY = 6;  // red; priv open lights it with the yellow hold led
const byte PIN_BUZZER = 8;  // active buzzer
const byte PIN_SERVO = 9;
const byte PIN_SONAR_TRIG = 11;
const byte PIN_SONAR_ECHO = 10;

// note: angles fit the servo as mounted on the table, C at one end and hold behind it at the other
const byte GATE_A = 90;
const byte GATE_B = 150;
const byte GATE_C = 180;
// note: rest is the hold position, so a gate that gets no valid decision stays parked
const byte GATE_REST = 0;

const int ARRIVAL_CM = 12;        // parcel closer than this counts as arrived
const unsigned long LIGHT_MS = 2500;

Servo gate;
String line;
bool parcelPresent = false;
byte nearScore = 0;
// note: the sonar flickers between near and far on soft or angled objects, so
// presence is a leaky score (+1 near, -1 far, 60 ms per read) instead of one read
const byte ARRIVE_SCORE = 5;
const byte MAX_SCORE = 20;
unsigned long lightsOffAt = 0;

void allLightsOff() {
  for (byte pin = PIN_LED_A; pin <= PIN_LED_DENY; pin++) digitalWrite(pin, LOW);
}

void showMessage(const String &text) {
#if HAS_LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(text.substring(0, 16));
  if (text.length() > 16) {
    lcd.setCursor(0, 1);
    lcd.print(text.substring(16, 32));
  }
#endif
}

void beep(byte times, int ms) {
  for (byte i = 0; i < times; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delay(ms);
    digitalWrite(PIN_BUZZER, LOW);
    if (i + 1 < times) delay(ms);
  }
}

void light(byte pin) {
  allLightsOff();
  digitalWrite(pin, HIGH);
  lightsOffAt = millis() + LIGHT_MS;
}

int readDistanceCm() {
  digitalWrite(PIN_SONAR_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_SONAR_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_SONAR_TRIG, LOW);
  unsigned long us = pulseIn(PIN_SONAR_ECHO, HIGH, 25000);
  if (us == 0) return -1;
  return us / 58;
}

void routeTo(char bin) {
  if (bin == 'A') { gate.write(GATE_A); light(PIN_LED_A); }
  else if (bin == 'B') { gate.write(GATE_B); light(PIN_LED_B); }
  else if (bin == 'C') { gate.write(GATE_C); light(PIN_LED_C); }
  else { Serial.println(F("ERR bad-bin")); return; }
  beep(1, 60);
  showMessage(String("BIN ") + bin);
  Serial.print(F("OK BIN "));
  Serial.println(bin);
}

void handle(const String &cmd) {
  if (cmd == "PING") {
    Serial.println(F("PONG"));
  } else if (cmd == "DIST") {
    Serial.print(F("DIST "));
    Serial.println(readDistanceCm());
  } else if (cmd.startsWith("BIN ") && cmd.length() == 5) {
    routeTo(cmd.charAt(4));
  } else if (cmd == "HOLD") {
    gate.write(GATE_REST);
    light(PIN_LED_HOLD);
    beep(2, 120);
    showMessage("HOLD");
    Serial.println(F("OK HOLD"));
  } else if (cmd == "DENY") {
    gate.write(GATE_REST);
    light(PIN_LED_DENY);
    beep(3, 200);
    showMessage("DENY");
    Serial.println(F("OK DENY"));
  } else if (cmd == "PRIV OPEN") {
    light(PIN_LED_HOLD);
    digitalWrite(PIN_LED_DENY, HIGH);
    beep(1, 400);
    showMessage("PRIV OPEN");
    Serial.println(F("OK PRIV OPEN"));
  } else if (cmd.startsWith("LCD ")) {
    showMessage(cmd.substring(4));
    Serial.println(F("OK LCD"));
  } else {
    Serial.println(F("ERR unknown"));
  }
}

void setup() {
  for (byte pin = PIN_LED_A; pin <= PIN_LED_DENY; pin++) pinMode(pin, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_SONAR_TRIG, OUTPUT);
  pinMode(PIN_SONAR_ECHO, INPUT);
  gate.attach(PIN_SERVO);
  gate.write(GATE_REST);
#if HAS_LCD
  lcd.begin(16, 2);
#endif
  showMessage("PAPERWEIGHT");
  Serial.begin(115200);
  Serial.println(F("READY"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      line.trim();
      if (line.length()) handle(line);
      line = "";
    } else if (line.length() < 40) {
      line += c;
    }
  }

  int cm = readDistanceCm();
  bool near = cm > 0 && cm < ARRIVAL_CM;
  if (near && nearScore < MAX_SCORE) nearScore++;
  if (!near && nearScore > 0) nearScore--;
  if (!parcelPresent && nearScore >= ARRIVE_SCORE) {
    parcelPresent = true;
    nearScore = MAX_SCORE;
    Serial.print(F("ARRIVAL "));
    Serial.println(cm);
  } else if (parcelPresent && nearScore == 0) {
    parcelPresent = false;
    Serial.println(F("DEPARTURE"));
  }

  if (lightsOffAt && millis() > lightsOffAt) {
    allLightsOff();
    gate.write(GATE_REST);
    lightsOffAt = 0;
  }
  delay(60);
}
