/*
  arm_controller.ino
  -------------------
  Runs on the STM32U585 (MCU) side of the Arduino UNO Q.

  Responsibilities (real-time side):
    - Drive the robotic arm's servo motors (joints + gripper) via
      hardware PWM.
    - Apply safety limits so no joint is commanded outside its safe
      range of motion.
    - Listen for target-position commands sent from the MPU (Linux/Python)
      side over the internal UNO Q bridge / serial link.

  All perception (camera input, hand tracking, gesture interpretation)
  happens on the MPU side in app/main.py, which sends this sketch simple
  text commands — this side only executes them.
*/

#include <Arduino.h>
#include <Servo.h>

// Adjust pin numbers and joint count to match your physical arm.
const int NUM_JOINTS = 4;                          // e.g. base, shoulder, elbow, wrist
const int JOINT_PINS[NUM_JOINTS] = {3, 5, 6, 9};
const int GRIPPER_PIN = 10;

const int GRIPPER_OPEN_ANGLE  = 30;
const int GRIPPER_CLOSE_ANGLE = 110;

// Per-joint safe operating limits — tune these to your arm's mechanical range.
const int JOINT_MIN_ANGLE[NUM_JOINTS] = {0, 20, 10, 0};
const int JOINT_MAX_ANGLE[NUM_JOINTS] = {180, 160, 170, 180};

Servo joints[NUM_JOINTS];
Servo gripper;
int currentAngle[NUM_JOINTS];

String inputBuffer = "";

void setup() {
  // initialises the servos, moves to a safe home position, and opens the serial link
  for (int i = 0; i < NUM_JOINTS; i++) {
    joints[i].attach(JOINT_PINS[i]);
    currentAngle[i] = 90;
  }
  gripper.attach(GRIPPER_PIN);

  goHome();
  openGripper();

  Serial.begin(115200);
  while (!Serial) { ; }
  Serial.println("arm_controller: MCU side ready");
}

void loop() {
  // continuously checks for incoming target-position commands from the MPU side
  readSerialMessage();
}

void readSerialMessage() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      handleMessage(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

// Expected message formats from app/arm_bridge.py (control_servos / control_gripper):
//   SERVO:<j0>:<j1>:<j2>:<j3>     e.g. SERVO:90:120:60:100
//   GRIP:CLOSE
//   GRIP:OPEN
//   HOME
void handleMessage(const String &msg) {
  if (msg.startsWith("SERVO:")) {
    applyJointCommand(msg.substring(6));
    ack("SERVO");
  } else if (msg == "GRIP:CLOSE") {
    closeGripper();
    ack("GRIP:CLOSE");
  } else if (msg == "GRIP:OPEN") {
    openGripper();
    ack("GRIP:OPEN");
  } else if (msg == "HOME") {
    goHome();
    ack("HOME");
  }
}

void ack(const String &what) {
  Serial.print("ACK:");
  Serial.println(what);
}

// map_servo_positions() on the MPU side already computes target angles;
// this just parses and applies them, enforcing each joint's safe limits.
void applyJointCommand(String payload) {
  int targets[NUM_JOINTS];
  int startIdx = 0;
  for (int i = 0; i < NUM_JOINTS; i++) {
    int sep = payload.indexOf(':', startIdx);
    String token = (sep == -1) ? payload.substring(startIdx) : payload.substring(startIdx, sep);
    targets[i] = constrain(token.toInt(), JOINT_MIN_ANGLE[i], JOINT_MAX_ANGLE[i]);
    startIdx = sep + 1;
    if (sep == -1) break;
  }

  for (int i = 0; i < NUM_JOINTS; i++) {
    joints[i].write(targets[i]);
    currentAngle[i] = targets[i];
  }
}

void openGripper() {
  gripper.write(GRIPPER_OPEN_ANGLE);
}

void closeGripper() {
  gripper.write(GRIPPER_CLOSE_ANGLE);
}

void goHome() {
  for (int i = 0; i < NUM_JOINTS; i++) {
    joints[i].write(90);
    currentAngle[i] = 90;
  }
}
