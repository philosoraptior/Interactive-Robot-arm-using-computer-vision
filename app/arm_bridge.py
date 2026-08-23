"""
arm_bridge.py
--------------
Sends servo/gripper commands from the MPU (Linux/Python) side to the MCU
(STM32U585 / arm_controller.ino) side over the UNO Q's internal serial
link, so the arm moves in real time as gestures are interpreted.
"""

import serial


class ArmBridge:
    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200):
        try:
            self._serial = serial.Serial(port, baudrate, timeout=1)
        except Exception as exc:
            print(f"arm_bridge: could not open {port} ({exc}); commands will only be printed")
            self._serial = None

    def _send(self, message: str):
        if self._serial is not None:
            self._serial.write(f"{message}\n".encode("ascii"))

    def control_servos(self, joint_angles: list):
        """Sends the calculated joint angles to the MCU side."""
        payload = ":".join(str(int(a)) for a in joint_angles)
        self._send(f"SERVO:{payload}")

    def control_gripper(self, close: bool):
        """Opens or closes the gripper based on the interpreted gesture."""
        self._send("GRIP:CLOSE" if close else "GRIP:OPEN")

    def home(self):
        self._send("HOME")
