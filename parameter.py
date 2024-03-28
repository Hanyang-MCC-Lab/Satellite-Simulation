# degree
import math

from vpython import vpython

LASER_ANGLE_THRESHOLD = 0.0000025 # 0.025밀리라디안
LASER_DISTANCE_THRESHOLD = 1
ANGULAR_VELOCITY = 0.00057595865 + 0.001093099711 # 0.033도
HANDOVER_TIME = 4000  # milli second
# second
PAT_DELAY = 4

SEOUL_LAT, SEOUL_LON = 37.56, 126.97
LA_LAT, LA_LON = 34.01, -118.41

real_rot_speed_per_second = 0.06263
SLOT_DURATION = 500 # 1000 = 1s
ANGULAR_VELOCITY_PER_SLOT = ANGULAR_VELOCITY * (SLOT_DURATION/1000)
CONST_SAT_DT = real_rot_speed_per_second * (SLOT_DURATION/1000)  # 위성 공전 각도: 1초당 회전 각도, 하루 15.03회 공전

v = vpython.color()
CONST_COLORS = [v.red, v.blue, v.green, v.white]