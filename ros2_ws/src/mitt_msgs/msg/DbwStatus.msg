# MITT drive-by-wire status: Teensy 4.1 -> laptop over micro-ROS.
#
# Spec: docs/design/dbw.md 10.1. Published at >= 50 Hz on the SAME link and
# the SAME clock as DbwCommand -- that is the point of ADR-SW1. A single
# `ros2 topic echo` therefore shows both sides of the control loop.

builtin_interfaces/Time stamp

# Measured absolute road-wheel angle in RADIANS, from the load-side sensor
# (docs/design/dbw.md ADR B). Authoritative -- never derived from the motor
# encoder, which sits upstream of the gearbox backlash.
float32 steering_angle

# The setpoint the position loop is currently tracking, echoed back so
# commanded-vs-measured can be compared from one bag on one time axis.
float32 steering_setpoint

# Longitudinal speed in m/s from the drive encoder.
float32 wheel_speed

# Cumulative drive-encoder ticks. PPR is a MEASURED constant recorded in
# config/calibration/ -- do NOT assume 52 (finding F7: the source project
# contradicts itself, 52 PPR in firmware vs 16 PPR in its own BOM).
int32 drive_ticks

# Authority mode -- see the state machine in docs/design/dbw.md 10.3.
uint8 MODE_ESTOP=0
uint8 MODE_MANUAL_RC=1
uint8 MODE_AUTONOMOUS=2
uint8 mode

# Fault bitfield. Any bit set is a reason the supervisor may refuse to leave
# ESTOP; see the FMEA in docs/design/safety.md 7.
uint16 FAULT_ENCODER=1        # angle sensor NAK / out of range / magnet lost
uint16 FAULT_SETPOINT_STALE=2 # no DbwCommand within 500 ms
uint16 FAULT_AT_LIMIT=4       # steering at a mechanical stop
uint16 FAULT_STALL=8          # encoder velocity ~0 under commanded effort
uint16 FAULT_RC_LOSS=16       # SBUS frame timeout
uint16 FAULT_OVER_CURRENT=32  # motor driver reported over-current
uint16 faults
