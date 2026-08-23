# ✋ Interactive Robot Arm Using Computer Vision

[![Track: Robotics & Gaming — Interactive AI](https://img.shields.io/badge/Track-Robotics%20%26%20Gaming%20--%20Interactive%20AI-blue)](https://github.com)
[![Board: Arduino UNO Q](https://img.shields.io/badge/Board-Arduino%20UNO%20Q-teal)](https://github.com)

**Team:**\
**Team Members:** Eshansh Singh (Team Leader — Computer Vision, Software &
System Integration)\ Shivanshi Shukla\
**Institution:** DIT, Dehradun, Uttarakhand \SRM Institute of Science and
Technology (SRMIST), Modinagar, Uttar Pradesh\
**Track:** Robotics & Gaming, Interactive AI\
**Board:** Arduino UNO Q (Qualcomm® Dragonwing™ QRB2210 + STM32U585)\


---

## 📌 Project Overview

Traditional robotic arms are usually operated with joysticks, buttons, or
predefined sequences — interfaces that can be confusing for beginners.
This project explores a more natural way for humans to interact with
robots: **hand gestures and movements directly command a 6-DOF robotic
arm.**

A camera captures the user's hand in real time, and a computer-vision
pipeline identifies hand landmarks and interprets movement and gestures as
control commands. By moving their hand and performing predefined gestures,
the user can command the arm and operate its end-effector to **grab, grip,
and release objects** — connecting visual perception directly to physical
actuation.

The project uses the UNO Q's **dual-brain architecture**:

1. **Qualcomm® Dragonwing™ QRB2210 (MPU):** Runs Debian Linux, handling
   camera input, computer-vision processing, and gesture interpretation —
   demanding significantly more processing power than a typical
   microcontroller-only system.
2. **STM32U585 Microcontroller (MCU):** Handles precise, real-time
   hardware interaction and servo control, executing the joint and
   gripper commands produced by the vision pipeline.

Running perception locally on the MPU reduces dependence on cloud services
and provides a direct path from detecting a gesture to producing a
physical response.

---

## 🛠️ Hardware Architecture & Components

- **Compute:** Arduino UNO Q (A)
- **Arm:** 6-DOF robotic arm assembly
- **Actuators:** 4× servo motors (joints) + 1× robotic gripper/end-effector
- **Vision:** USB / local webcam
- **Power:** External variable servo power supply (kept separate from the
  UNO Q's own supply)
- **Other:** Connecting wires/cables, mechanical brackets/links/fasteners,
  laptop (for development/monitoring)

See the full Bill of Materials in the project report for details.

---

## 🤖 Vision / Gesture Model

- **Model used:** Custom TFLite-based hand-landmark model (MediaPipe
  Hands).
- **Training platform:** MediaPipe / TensorFlow Lite.
- **What it does:** Detects the hand in each camera frame and extracts
  landmark coordinates, which are used to interpret position and pinch
  gestures instead of physical buttons or a joystick.
- **Known limitations:** Performance degrades if the hand is outside the
  camera's view, partially occluded, moving too fast, poorly lit, or set
  against a complex background. Camera frame rate and processing delay
  also affect how responsive the arm appears.

---

## 💻 Quick Start & Software Setup

### 1. Arm firmware (MCU side)

1. Open `firmware/arm_controller/arm_controller.ino` in the **Arduino IDE**
   or **Arduino App Lab**.
2. Select your **Arduino UNO Q** board target and check the servo pin
   assignments (`JOINT_PINS`, `GRIPPER_PIN`) and per-joint safe angle
   limits match your physical arm.
3. Flash the sketch — it listens for `SERVO:`, `GRIP:` and `HOME` commands
   from the MPU side and drives the servos in real time.

### 2. Vision + gesture app (MPU side)

1. `cd app && pip install -r requirements.txt`
2. `python main.py --camera 0`

This opens a live dashboard window showing the camera feed, detected hand
skeleton, current gripper state, and joint angles, while continuously
driving the arm from your hand movements.

---

## 💻 Code Structure

The software is organised into four main stages: **camera input, hand
tracking, gesture interpretation, and robotic arm control** (all in
`app/main.py`, with hardware commands sent via `app/arm_bridge.py`):

- **`camera_input()`** — captures real-time video frames from the webcam
  connected to the Arduino UNO Q and feeds them to the vision pipeline.
- **`detect_hand()`** — processes each camera frame and detects the
  user's hand, extracting the landmark coordinates used for tracking hand
  position and identifying gestures.
- **`interpret_gesture()`** — analyses the detected hand landmarks and
  converts predefined hand movements and gestures into corresponding
  robotic-arm commands.
- **`map_servo_positions()`** — converts the interpreted hand movement
  into target servo angles, kept within the arm's defined operating
  limits.
- **`control_servos()`** — sends the calculated position commands to the
  corresponding servo motors, enabling coordinated 6-DOF arm movement.
- **`control_gripper()`** — interprets the designated gripping gesture and
  controls the end-effector to grab, hold, or release an object.
- **`update_dashboard()`** — shows real-time system information such as
  the camera preview and servo-position data for monitoring the arm.
- **`main()`** — continuously executes the complete control loop: camera
  capture → hand detection → gesture interpretation → servo-position
  mapping → robotic arm movement.

---

## 💡 Key Engineering Challenges

1. **Translating vision output into smooth motion:** Raw hand-landmark
   positions fluctuate between frames; feeding this noise directly into
   servo commands caused unstable, jerky movement.
2. **Coordinating multiple servos within mechanical limits:** Driving
   several joints together while respecting the 6-DOF arm's safe range of
   motion — and separating servo power requirements from the controller's
   own computational needs — required careful design.
3. **Reliable hand detection under real-world conditions:** Camera angle,
   lighting, occlusion, and background complexity all affect detection
   reliability, so the software has to handle brief detection failures
   safely rather than allowing uncontrolled movement.

---

## 📊 Current Capabilities & Roadmap

- [x] Real-time hand detection and landmark extraction (MediaPipe)
- [x] Gesture-to-servo-angle mapping
- [x] Pinch-gesture gripper control (grab / hold / release)
- [x] Live dashboard for monitoring camera feed and joint state
- [ ] Motion smoothing for steadier, less jerky arm movement *(planned)*
- [ ] Measured latency/accuracy benchmarking *(planned)*
- [ ] Per-joint safety limit tuning and testing *(planned)*
- [ ] Object detection for semi-autonomous grasping *(planned)*
- [ ] Inverse-kinematics-based end-effector control *(planned)*
- [ ] Adaptive gesture mapping *(planned)*

---

## 🌐 Open-Source Impact

This project is released as an open-source framework — firmware, vision
pipeline, and documentation — so other teams can build on it for
gesture-controlled robotics on the UNO Q platform without starting from
scratch.

---

## Credits & Acknowledgments

Built by **Eshansh Singh** and **Shivanshi Shukla** on the **Arduino UNO
Q** platform, using **MediaPipe** for hand-landmark detection.

---

## ⚠️ Disclaimer

*This is an experimental, educational project developed for a hackathon/
competition submission. This framework is provided **"AS IS"**, without
warranty of any kind. Operate experimental hardware at your own risk and
observe standard safety precautions around moving mechanical parts.*
