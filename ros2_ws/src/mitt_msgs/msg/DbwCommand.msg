# MITT drive-by-wire command: laptop -> Teensy 4.1 over micro-ROS.
#
# Spec: docs/design/dbw.md 10.1 and the numeric interface contract in 12.
# Published at >= 50 Hz. Staleness > 500 ms drops the vehicle to ESTOP
# (docs/design/safety.md failsafe row 1).

builtin_interfaces/Time stamp

# Road-wheel steering angle in RADIANS, not degrees.
# Clamped by firmware to +/- 0.3927 rad (+/- 22.5 deg).
float32 steering_angle

# Signed longitudinal speed in m/s. Positive is forward.
# Firmware applies ramp limiting, a speed cap, and a direction interlock
# before this reaches the motor driver (docs/design/dbw.md 7).
float32 speed
