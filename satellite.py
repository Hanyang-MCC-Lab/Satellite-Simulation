import math
from vpython import *
from operator import mul


class Satellite:
    # 위성 객체의 attribute
    sat_attr = sphere()
    orbit = None
    id = "SAT-"
    # 위도, 경도, 고도(지구 반지름 + LEO 평균 고도)
    longitude = 0
    latitude = 0
    altitude = 6371 + 550
    # ECEF 좌표계상의 x, y, z좌표
    x, y, z = 0, 0, 0

    def __init__(self, orbit, sat_index, inclination, omega):
        self.id = self.id + sat_index
        self.orbit = orbit
        # 위도, 경도
        self.latitude = math.asin(math.sin(inclination) * math.sin(omega))
        self.longitude = math.atan2(
            math.cos(inclination) * math.sin(omega) * math.cos(omega) + 360) % 360 + orbit.ascend_lon
        # ECEF 좌표
        self.x = math.cos(self.latitude) * math.cos(self.longitude) * self.altitude
        self.y = math.cos(self.latitude) * math.sin(self.longitude) * self.altitude
        self.z = math.sin(self.latitude) * self.altitude
        # 구체 attribute 설정
        self.sat_attr.pos = vec(self.y, self.z, self.x)
        self.sat_attr.axis = vec(1, 0, 0)  # 바라보는 방향이라는데 정확한 의미는 모름
        self.sat_attr.radius = 60
        self.sat_attr.color = color.white

    def get_geo_info(self):
        info = {
            "lon": self.longitude,
            "lat": self.latitude,
            "alt": self.altitude
        }
        return info

    def get_ecef_info(self):
        info = {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
        return info
