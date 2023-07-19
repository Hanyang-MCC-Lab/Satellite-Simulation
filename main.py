'Python 3.7'
'Web VPython 3.2'
from vpython import *
from tkinter import *
import math

# 상수선언
CONST_EARTH_RADIUS = 6371  # 지구반경
CONST_SAT_RADIUS = CONST_EARTH_RADIUS + 550  # 지구반경 + 550KM
CONST_ORBIT_NUM = 72  # 궤도개수
CONST_SAT_NUM = 22  # 위성개수
CONST_ORBIT_ROT = 0.0873  # 궤도회전각도 라디안 5도
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
    orbit_attr = None

    def __init__(self, index, inclination, lon_of_ascending):
        self.id = self.id + str(index)
        self.inclination = inclination
        self.lon_of_ascending = lon_of_ascending
        # 궤도 회전 -1을 넣은 이유는 45~47번 코드를 주석해제해서 실행시켜보면 궤도가 xz평면기준으로 반대로 되어있었음을 알 수 있음
        self.orbit_attr = ring(pos=vec(0, 0, 0),
                               axis=vec(math.sin(lon_of_ascending) * 0 + math.cos(lon_of_ascending) * math.sin(
                                   -1 * inclination),
                                        math.cos(-1 * inclination),
                                        math.cos(lon_of_ascending) * 0 - math.sin(lon_of_ascending) * math.sin(
                                            -1 * inclination)),
                               color=color.red, thickness=15, radius=self.semi_major_axis)
        # 위성 배치
        for idx in range(CONST_SAT_NUM):
            sat = Satellite(self, idx, inclination, idx * CONST_SAT_ROT)
            self.satellites.append(sat)
            # 아래 코드 주석 해제하면 각 위성이 가진 ECEF, LLH좌표 확인가능
            print(sat.get_llh_info())
            print(sat.get_ecef_info())
            sleep(0.1)

    def get_orbit_info(self):
        info = {
            "semi-major axis": self.semi_major_axis,
            "inclination": self.inclination,
            "longitude of the ascending node": self.lon_of_ascending
        }
        return info


class Satellite:
    # 위성 객체의 attribute
    sat_attr = None
    orbit = None
    id = "SAT-"
    # 위도, 경도, 고도(지구 반지름 + LEO 평균 고도)
    longitude = 0
    latitude = 0
    altitude = 550
    # ECEF 좌표계상의 x, y, z좌표
    x, y, z = 0, 0, 0

    def __init__(self, orbit, sat_index, inclination, theta):
        self.id = self.id + str(sat_index)
        self.orbit = orbit
        # 위도, 경도
        self.latitude = math.asin(math.sin(inclination) * math.sin(theta))
        self.longitude = (math.atan2(math.cos(inclination) * math.sin(theta),
                                     math.cos(theta)) + 6.2832) % 6.2832 + orbit.lon_of_ascending
        # ECEF 좌표
        self.x = math.cos(self.latitude) * math.cos(self.longitude) * (6371 + self.altitude)
        self.y = math.cos(self.latitude) * math.sin(self.longitude) * (6371 + self.altitude)
        self.z = math.sin(self.latitude) * (6371 + self.altitude)
        # 구체 attribute 설정
        self.sat_attr = sphere(pos=vec(self.y, self.z, self.x), axis=vec(0, 0, 1), radius=60, color=color.white)

    # 위성의 LLH를 GET하는 메소드, 다만 라디안으로 저장되어 있어 일반 degree로 변환이 필요함(지금은 안되어 있음)
    def get_llh_info(self):
        info = {
            "lon": math.degrees(self.longitude),
            "lat": math.degrees(self.latitude),
            "alt": self.altitude
        }
        return info

    # 위성의 ECEF 좌표를 GET하는 메소드
    def get_ecef_info(self):
        info = {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
        return info


# 클래스 끝, 메인 로직 시작

# 궤도 및 위성 리스트 생성
orbits = []
sat = []

# 모니터 해상도에 따라 유동적인 해상도 조절
root = Tk()
monitor_height = root.winfo_screenheight()
monitor_width = root.winfo_screenwidth()

# 케플러 요소 입력

# 씬 구성
# 기준 춘분점(Reference direction vector = (0, 0, 1))
scene = canvas(width=monitor_width - 15, height=monitor_height - 15)
scene.resizable = False

# xy평면과 x, y, z축 pos=vec(y방향, z방향, x방향)
mybox = box(pos=vec(0, 0, 0), length=30000, height=1, width=30000, opacity=0.5)
lineX = arrow(pos=vec(-15000, 0, 0), axis=vec(1, 0, 0), shaftwidth=50, headwidth=300, headlength=300, length=30000,
              color=color.magenta)
lineY = arrow(pos=vec(0, 0, -15000), axis=vec(0, 0, 1), shaftwidth=50, headwidth=300, headlength=300, length=30000,
              color=color.blue)
lineZ = arrow(pos=vec(0, -10000, 0), axis=vec(0, 1, 0), shaftwidth=50, headwidth=300, headlength=300, length=20000,
              color=color.green)
t1 = text(pos=vec(-15000, 500, 0), text="Vernal equinox", align='center', billboard=True, color=color.cyan,
          emissive=True)

earth = sphere(pos=vec(0, 0, 0), radius=CONST_EARTH_RADIUS, texture=textures.earth)  # 지구생성
inclination = math.radians(float(input("Please input Orbit Inclination radian.\n Orbit Inclination : ")))  # 궤도경사

# 이중for문을 통하여 궤도 및 위성 배치
for i in range(CONST_ORBIT_NUM):  # 궤도생성
    orbits.append(Orbit(i, inclination, CONST_ORBIT_ROT * i))

    # orbit.append(ring(pos=vec(0, 0, 0),
    #                   #궤도경사 회전 및 궤도 축 회전
    #                   axis=vec(math.cos(CONST_ORBIT_ROT * i) * 0 - math.sin(CONST_ORBIT_ROT * i) * math.sin(inclination),
    #                            math.cos(inclination),
    #                            math.sin(CONST_ORBIT_ROT * i) * 0 + math.cos(CONST_ORBIT_ROT * i) * math.sin(inclination)),
    #                   radius=CONST_SAT_RADIUS, color=color.red, thickness=15))
    #
    # for j in range(CONST_SAT_NUM): #위성생성
    #                         #궤도경사 회전 및 궤도 축 회전 및 궤도회전
    #     sat.append(sphere(pos=vec(math.cos(CONST_ORBIT_ROT * i) * math.cos(CONST_SAT_ROT * j) * CONST_SAT_RADIUS - math.sin(CONST_ORBIT_ROT * i) * math.cos(inclination) * math.sin(CONST_SAT_ROT * j) * CONST_SAT_RADIUS,
    #                               0 - math.sin(inclination) * math.sin(CONST_SAT_ROT * j) * CONST_SAT_RADIUS,
    #                               math.sin(CONST_ORBIT_ROT * i) * math.cos(CONST_SAT_ROT * j) * CONST_SAT_RADIUS + math.cos(CONST_ORBIT_ROT * i) * math.cos(inclination) * math.sin(CONST_SAT_ROT * j) * CONST_SAT_RADIUS),
    #                       axis=vec(1, 0, 0), radius=60, color=color.white))
