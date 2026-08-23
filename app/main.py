"""
main.py
-------
Runs on the MPU (Linux/Debian) side of the Arduino UNO Q.

Interactive Robot Arm using Computer Vision — a webcam-driven, hand-gesture
controlled robotic arm. A MediaPipe hand-landmark model (TFLite-based)
detects the user's hand in each frame; hand position and pinch gesture are
converted into servo target angles and a gripper open/close command, which
are sent to the MCU side (firmware/arm_controller/arm_controller.ino) for
real-time execution.

Pipeline (matches the project report's Code Structure section):
  camera_input() -> detect_hand() -> interpret_gesture()
    -> map_servo_positions() -> control_servos() / control_gripper()
    -> update_dashboard()

Usage:
  python main.py --camera 0
"""

import argparse
import math

import cv2
import mediapipe as mp

from arm_bridge import ArmBridge

# --- Gesture / mapping tuning ---
PINCH_CLOSE_THRESHOLD = 0.06   # normalised distance between thumb tip & index tip
NUM_JOINTS = 4                  # base, shoulder, elbow, wrist — match arm_controller.ino
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# MediaPipe Hands landmark indices used below
WRIST = 0
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_TIP = 8
MIDDLE_MCP = 9

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def camera_input(camera_index: int):
    """Captures real-time video frames from the webcam connected to the UNO Q."""
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return camera


def detect_hand(hands_model, frame):
    """
    Processes a camera frame and detects the user's hand, extracting
    hand-landmark coordinates required for tracking hand position and
    identifying gestures. Returns the MediaPipe landmark list, or None if
    no hand is detected in this frame.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands_model.process(rgb_frame)
    if not results.multi_hand_landmarks:
        return None
    return results.multi_hand_landmarks[0]


def _landmark_xy(landmarks, index):
    lm = landmarks.landmark[index]
    return lm.x, lm.y


def interpret_gesture(landmarks):
    """
    Analyses the detected hand landmarks and converts predefined hand
    movements and gestures into corresponding robotic-arm commands.

    Returns a dict:
      {
        "hand_x": float (0-1, normalised),
        "hand_y": float (0-1, normalised),
        "hand_span": float (wrist-to-middle-MCP distance, proxy for reach),
        "wrist_angle_deg": float (hand tilt, used for wrist rotation),
        "pinch": bool (True = gripper should close),
      }
    """
    wrist_x, wrist_y = _landmark_xy(landmarks, WRIST)
    middle_x, middle_y = _landmark_xy(landmarks, MIDDLE_MCP)
    thumb_x, thumb_y = _landmark_xy(landmarks, THUMB_TIP)
    index_x, index_y = _landmark_xy(landmarks, INDEX_TIP)

    hand_span = math.hypot(middle_x - wrist_x, middle_y - wrist_y)
    wrist_angle_deg = math.degrees(math.atan2(middle_y - wrist_y, middle_x - wrist_x))
    pinch_distance = math.hypot(thumb_x - index_x, thumb_y - index_y)
    pinch = pinch_distance < PINCH_CLOSE_THRESHOLD

    return {
        "hand_x": wrist_x,
        "hand_y": wrist_y,
        "hand_span": hand_span,
        "wrist_angle_deg": wrist_angle_deg,
        "pinch": pinch,
    }


def map_servo_positions(gesture: dict):
    """
    Converts the interpreted hand movement into suitable target angles for
    the servo motors, keeping commanded positions within the arm's defined
    operating limits (hard safety limits are also enforced again on the
    MCU side in arm_controller.ino).

    Returns a list of NUM_JOINTS target angles in degrees [0, 180].
    """
    # Joint 0 — base rotation: left/right hand position
    base = int(gesture["hand_x"] * 180)

    # Joint 1 — shoulder: up/down hand position (inverted: hand up -> arm up)
    shoulder = int((1.0 - gesture["hand_y"]) * 180)

    # Joint 2 — elbow: hand span as a rough proxy for reach/distance from camera
    elbow = int(min(max(gesture["hand_span"] * 400, 0), 180))

    # Joint 3 — wrist: hand tilt angle, offset and clamped to a sensible range
    wrist = int(min(max(90 + gesture["wrist_angle_deg"], 0), 180))

    angles = [base, shoulder, elbow, wrist]
    return [min(max(a, 0), 180) for a in angles][:NUM_JOINTS]


def control_servos(arm: ArmBridge, joint_angles: list):
    """Sends the calculated position commands to the corresponding servo motors."""
    arm.control_servos(joint_angles)


def control_gripper(arm: ArmBridge, close: bool):
    """Interprets the designated gripping gesture and controls the end-effector."""
    arm.control_gripper(close)


def update_dashboard(frame, landmarks, gesture: dict, joint_angles: list):
    """
    Provides real-time system information — camera preview and
    servo-position overlay — for monitoring the operation of the robotic
    arm. Draws the hand skeleton and current joint angles on the frame.
    """
    if landmarks is not None:
        mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

    status = "GRIP" if gesture and gesture["pinch"] else "OPEN"
    cv2.putText(frame, f"Gripper: {status}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Joints: {joint_angles}", (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("Interactive Robot Arm — Dashboard", frame)


def main():
    """
    Continuously executes the complete control loop: camera capture -> hand
    detection -> gesture interpretation -> servo-position mapping ->
    robotic arm movement.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()

    camera = camera_input(args.camera)
    arm = ArmBridge()
    arm.home()

    print("main.py: running. Press 'q' in the dashboard window, or Ctrl+C, to stop.")

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands_model:
        try:
            while True:
                ok, frame = camera.read()
                if not ok:
                    continue

                landmarks = detect_hand(hands_model, frame)
                joint_angles = [90] * NUM_JOINTS
                gesture = None

                if landmarks is not None:
                    gesture = interpret_gesture(landmarks)
                    joint_angles = map_servo_positions(gesture)
                    control_servos(arm, joint_angles)
                    control_gripper(arm, gesture["pinch"])

                update_dashboard(frame, landmarks, gesture, joint_angles)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            print("\nShutting down.")
        finally:
            camera.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
