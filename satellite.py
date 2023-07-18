import math
from operator import mul
class Satellite:
    # 위성 객체의 attribute

    id = "undefined"
    # 위도, 경도, 고도(지구 반지름 + LEO 평균 고도)
    longitude = 0
    latitude = 0
    altitude = 6371 + 550
    # ECEF 좌표계상의 x, y, z좌표
    x, y, z = 0, 0, 0

    def __init__(self, index, inclination, omega):
        self.id = index
        # 위도, 경도 구하는 공식
        self.latitude = math.asin(mul(math.sin(inclination), math.sin(omega)))
        self.longitude = math.atan2()


    def get_geo_info(self):
        info = {
            "lon" : self.longitude,
            "lat" : self.latitude,
            "alt" : self.altitude
        }
        return info
    def get_ECEF_info(self):
        info = {
            "x" : self.x,
            "y" : self.y,
            "z" : self.z,
        }
