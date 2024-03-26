# degree
import math

from vpython import vpython

LASER_ANGLE_THRESHOLD = 0.003 # 3밀리라디안
LASER_DISTANCE_THRESHOLD = 1
ANGULAR_VELOCITY = 0.0005759586499999230303 # 0.033도
HANDOVER_TIME = 4000  # milli second
# second
PAT_DELAY = 4

SEOUL_LAT, SEOUL_LON = 37.56, 126.97
LA_LAT, LA_LON = 34.01, -118.41
orbitNum = 72
satNum = 22
maxDistance = 0
CONST_EARTH_RADIUS = 6371  # 지구반경
orbitRot = math.radians(360 / orbitNum)  # 궤도회전각도
satRot = math.radians(360 / satNum)  # 위성회전각도
real_rot_speed_per_second = 0.06263
SLOT_DURATION = 1000 # 1000 = 1s
CONST_SAT_DT = real_rot_speed_per_second * (SLOT_DURATION/1000)  # 위성 공전 각도: 1초당 회전 각도, 하루 15.03회 공전

v = vpython.color()
CONST_COLORS = [v.red, v.blue, v.green, v.white]