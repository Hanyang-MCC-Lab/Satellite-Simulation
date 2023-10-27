import math
from satellite import Satellite
from vpython import *

CONST_SAT_NUM = 22  # 위성개수
CONST_SAT_ROT = 0.2855  # 위성회전각도 라디안 16.3도


class Orbit:
    # 궤도 객체의 attribute
    id = "ORBIT-"
    # 궤도가 가진 위성 객체 (22개)
    satellites = []
    # 궤도 요소
    semi_major_axis = 6371 + 550  # km
    inclination = 0
    lon_of_ascending = 0
    # 궤도 모형
    orbit_attr = ring(pos=vec(0, 0, 0),
                      radius=semi_major_axis,
                      color=color.red, thickness=15)

    def __init__(self, index, inclination, lon_of_ascending):
        self.id = self.id + str(index)
        self.inclination = inclination
        self.lon_of_ascending = lon_of_ascending
        # 궤도 회전
        self.orbit_attr.axis = vec(math.sin(lon_of_ascending) * 0 + math.cos(lon_of_ascending) * math.sin(inclination),
                                   math.cos(inclination),
                                   math.cos(lon_of_ascending) * 0 - math.sin(lon_of_ascending) * math.sin(inclination))
        # 위성 배치
        for idx in range(CONST_SAT_NUM):
            self.satellites.append(Satellite(self, idx, inclination, idx * CONST_SAT_ROT))

    def get_orbit_info(self):
        info = {
            "semi-major axis": self.semi_major_axis,
            "inclination": self.inclination,
            "longitude of the ascending node": self.lon_of_ascending
        }
        return info
