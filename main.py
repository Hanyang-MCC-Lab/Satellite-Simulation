'Python 3.7'
import time

import vpython

'Web VPython 3.2'
from vpython import *
import pyautogui
import math

# 상수선언
orbitNum = 72
satNum = 22
CONST_EARTH_RADIUS = 6371  # 지구반경
# CONST_ORBIT_RADIUS = CONST_EARTH_RADIUS + 550  # 지구반경 + 550KM
orbitRot = math.radians(360 / orbitNum)  # 궤도회전각도
satRot = math.radians(360 / satNum)  # 위성회전각도
CONST_SAT_DT = math.radians(1)  # 위성 공전 각도
v = vpython.color()
CONST_COLORS = [v.red, v.blue, v.green, v.white]


class Orbit:
    # 궤도 객체의 attribute
    id = "ORBIT-"
    # # 궤도가 가진 위성 객체 (22개)
    # satellites = []
    # 궤도 요소
    semi_major_axis = 6371  # km
    inclination = 0
    lon_of_ascending = 0
    # 궤도 모형
    orbit_attr = None
    orbits = []

    def __init__(self, index, inclination, altitude, lon_of_ascending, color):
        self.orbits.append(self)
        self.satellites = []
        self.id = self.id + str(index)
        self.inclination = inclination
        self.lon_of_ascending = lon_of_ascending
        self.semi_major_axis = CONST_EARTH_RADIUS
        # 궤도 회전 -1을 넣은 이유는 45~47번 코드를 주석해제해서 실행시켜보면 궤도가 xz평면기준으로 반대로 되어있었음을 알 수 있음
        self.orbit_attr = ring(pos=vec(0, 0, 0), opacity=0.3,
                               axis=vec(math.sin(lon_of_ascending) * 0 + math.cos(lon_of_ascending) * math.sin(
                                   -1 * inclination),
                                        math.cos(-1 * inclination),
                                        math.cos(lon_of_ascending) * 0 - math.sin(lon_of_ascending) * math.sin(
                                            -1 * inclination)),
                               color=color, thickness=15, radius=self.semi_major_axis + altitude, )
        # 위성 배치
        for idx in range(satNum):
            sat = Satellite(self, idx, inclination, altitude, idx * satRot)
            self.satellites.append(sat)
            print(sat.id, "is appended in", self.id)
            # 아래 코드 주석 해제하면 각 위성이 가진 ECEF, LLH좌표 확인가능
            # print(sat.get_llh_info())
            # print(sat.get_ecef_info())
            # sleep(0.005)

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
    true_anomaly = 0
    # 위도, 경도, 고도(지구 반지름 + LEO 평균 고도)
    longitude = 0
    latitude = 0
    altitude = 550
    # ECEF 좌표계상의 x, y, z좌표
    x, y, z = 0, 0, 0

    def __init__(self, orbit: Orbit, sat_index, inclination, alt, theta):
        self.id = self.id + str(orbit.id[6:]) + "-" + str(sat_index)
        self.orbit = orbit
        self.true_anomaly = theta
        self.altitude = alt
        # 위도, 경도
        self.latitude = math.asin(math.sin(inclination) * math.sin(theta))
        self.longitude = (math.atan2(math.cos(inclination) * math.sin(theta),
                                     math.cos(theta)) + 6.2832) % 6.2832 + orbit.lon_of_ascending
        # ECEF 좌표
        self.x = math.cos(self.latitude) * math.cos(self.longitude) * (CONST_EARTH_RADIUS + self.altitude)
        self.y = math.cos(self.latitude) * math.sin(self.longitude) * (CONST_EARTH_RADIUS + self.altitude)
        self.z = math.sin(self.latitude) * (CONST_EARTH_RADIUS + self.altitude)
        # 구체 attribute 설정
        self.sat_attr = sphere(pos=vec(self.y, self.z, self.x), axis=vec(0, 0, 1), radius=60, color=color.white)

    # 위성의 LLH를 GET하는 메소드, 다만 라디안으로 저장되어 있어 일반 degree로 변환이 필요함(지금은 안되어 있음)
    def get_llh_info(self):
        info = {"ORBIT-ID": self.orbit.id,
                "SAT-ID": self.id,
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

    def get_sat_info(self):
        start_info = self.id.split("-")
        info = {"orbit": int(start_info[1]),
                "satellite": int(start_info[2]),
                }
        return info

    def refresh(self, dt):
        self.true_anomaly = (self.true_anomaly + dt) % 360
        # 위도, 경도
        self.latitude = math.asin(math.sin(self.orbit.inclination) * math.sin(self.true_anomaly))
        self.longitude = (math.atan2(math.cos(self.orbit.inclination) * math.sin(self.true_anomaly),
                                     math.cos(self.true_anomaly)) + 6.2832) % 6.2832 + self.orbit.lon_of_ascending
        # ECEF 좌표
        self.x = math.cos(self.latitude) * math.cos(self.longitude) * (CONST_EARTH_RADIUS + self.altitude)
        self.y = math.cos(self.latitude) * math.sin(self.longitude) * (CONST_EARTH_RADIUS + self.altitude)
        self.z = math.sin(self.latitude) * (CONST_EARTH_RADIUS + self.altitude)
        # 구체 attribute 재설정
        self.sat_attr.pos = vec(self.y, self.z, self.x)

    def find_proper(self, cur_info, horizontal, vertical):
        proper_sat = self
        right, left = ((cur_info["orbit"] + 1) + orbitNum) % orbitNum, ((cur_info["orbit"] - 1) + orbitNum) % orbitNum
        up, down = ((cur_info["satellite"] + 1) + satNum) % satNum, ((cur_info["satellite"] - 1) + satNum) % satNum
        if vertical > 0:
            if horizontal > 0:  # 위로, 동으로
                proper_sat = self.orbit.orbits[right].satellites[up]
            elif horizontal < 0:  # 위로, 서로
                proper_sat = self.orbit.orbits[left].satellites[up]
            else:  # 위로
                proper_sat = self.orbit.orbits[cur_info["orbit"]].satellites[up]

        elif vertical < 0:
            if horizontal > 0:  # 아래로, 동으로
                proper_sat = self.orbit.orbits[right].satellites[down]
            elif horizontal < 0:  # 아래로, 서로
                proper_sat = self.orbit.orbits[left].satellites[down]
            else:  # 아래로
                proper_sat = self.orbit.orbits[cur_info["orbit"]].satellites[down]
        else:
            if horizontal > 0:  # 동으로
                proper_sat = self.orbit.orbits[right].satellites[cur_info["satellite"]]
            else:  # 서로
                proper_sat = self.orbit.orbits[left].satellites[cur_info["satellite"]]

        return proper_sat

    def transfer(self, destination, path):
        print("packet is in", self.id)
        # sleep(1)
        path.append(self)
        if destination.id == self.id:
            return path
        else:
            dest_info = destination.get_sat_info()
            cur_info = self.get_sat_info()
            horizontal, vertical = 0, 0

            west_distance = ((cur_info["orbit"] - dest_info["orbit"]) + orbitNum) % orbitNum
            east_distance = ((dest_info["orbit"] - cur_info["orbit"]) + orbitNum) % orbitNum
            # print("west, east distance:", west_distance, east_distance)
            if west_distance <= east_distance and west_distance != 0:
                horizontal = -1
            elif west_distance > east_distance:
                horizontal = 1

            south_distance = ((cur_info["satellite"] - dest_info["satellite"]) + satNum) % satNum
            north_distance = ((dest_info["satellite"] - cur_info["satellite"]) + satNum) % satNum
            # print("north, south distance:", north_distance, south_distance)
            if north_distance <= south_distance and north_distance != 0:
                vertical = 1
            elif north_distance > south_distance:
                vertical = -1
            # print("horizontal, vertical:", horizontal, vertical)
            return self.find_proper(cur_info, horizontal, vertical).transfer(destination, path)


class Network:
    def __init__(self):
        self.log = []

    def get_euc_distance(self, node_A: Satellite, node_B: Satellite):
        node_A_ecef = list(node_A.get_ecef_info().values())
        node_B_ecef = list(node_B.get_ecef_info().values())
        print(node_A_ecef)
        print(node_B_ecef)
        print(math.dist(node_A_ecef, node_B_ecef))

    def routing(self, start: Satellite, dest: Satellite):
        start_time = time.perf_counter()
        path = start.transfer(dest, [])
        finish_time = time.perf_counter()
        delay = finish_time - start_time
        self.log.append({
            "packet": "Packet-"+start.id+"To"+dest.id,
            "delay": round(delay*1000, 6),
            "path": path,
        })



# 클래스 끝, 메인 로직 시작

# 궤도 및 위성 리스트 생성
constellations = []

# 모니터 해상도에 따라 능동적인 해상도 조절
M_size = pyautogui.size()
monitor_width = M_size[0]
monitor_height = M_size[1] - 100

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
t3 = text(text='Vernal equinox', pos=vec(0, 500, 15000), align='center', height=500,
          color=color.cyan, billboard=True, emissive=True, depth=0.15)
earth = sphere(pos=vec(0, 0, 0), radius=CONST_EARTH_RADIUS, texture=textures.earth)  # 지구생성

# 입력 GUI구성
running = True
setting = True
scene.caption = "\nOrbital inclination/    Altitude      / Orbits Number /Satellites Number\n\n"
scene.caption = "\nOrbital inclination / Altitude / Orbits Number / Satellites Number\n\n"


def Inc(i):
    return i.number


def Alt(a):
    return a.number


def OrbNum(o):
    return o.number


def SatNum(s):
    return s.number


def Set(s):
    global setting
    setting = not setting
    if setting:
        s.text = "Set"
    else:
        s.text = "Setting"


def Run(r):
    global running
    running = not running
    if running:
        r.text = "Run"
    else:
        r.text = "Runnning"


n = winput(bind=Inc, width=120, type="numeric")
i = winput(bind=Alt, width=120, type="numeric")
o = winput(bind=OrbNum, width=120, type="numeric")
s = winput(bind=SatNum, width=120, type="numeric")
button(text="Set", bind=Set)
button(text="Run", bind=Run)


# 이중for문을 통하여 궤도 및 위성 배치 함수
def deploy(inc, axis, color):
    orbits = []
    if int(math.degrees(inc)) is 90:
        for i in range(int(orbitNum / 2)):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
    else:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
    constellations.append(orbits)

    # 계산로직
    # orbit.append(ring(pos=vec(0, 0, 0),
    #                   #궤도경사 회전 및 궤도 축 회전
    #                   axis=vec(math.cos(orbitRot * i) * 0 - math.sin(orbitRot * i) * math.sin(inclination),
    #                            math.cos(inclination),
    #                            math.sin(orbitRot * i) * 0 + math.cos(orbitRot * i) * math.sin(inclination)),
    #                   radius=CONST_ORBIT_RADIUS, color=color.red, thickness=15))
    #
    # for j in range(satNum): #위성생성
    #                         #궤도경사 회전 및 궤도 축 회전 및 궤도회전
    #     sat.append(sphere(pos=vec(math.cos(orbitRot * i) * math.cos(satRot * j) * CONST_ORBIT_RADIUS - math.sin(orbitRot * i) * math.cos(inclination) * math.sin(satRot * j) * CONST_ORBIT_RADIUS,
    #                               0 - math.sin(inclination) * math.sin(satRot * j) * CONST_ORBIT_RADIUS,
    #                               math.sin(orbitRot * i) * math.cos(satRot * j) * CONST_ORBIT_RADIUS + math.cos(orbitRot * i) * math.cos(inclination) * math.sin(satRot * j) * CONST_ORBIT_RADIUS),
    #                       axis=vec(1, 0, 0), radius=60, color=color.white))


# 메인
orbit_cnt = 0
network = Network()
while 1:

    while setting == False:
        # 케플러요소 입력
        print("Setting")
        inclination = math.radians(float(Inc(n)))  # 궤도경사
        altitude = int(Alt(i))  # 궤도 반지름
        orbitNum = OrbNum(o)
        satNum = SatNum(s)
        orbitRot = math.radians(360 / orbitNum)
        satRot = math.radians(360 / satNum)
        deploy(inclination, altitude, CONST_COLORS[orbit_cnt])
        orbit_cnt = (orbit_cnt + 1) % 4
        setting = not setting

    while running == False:
        print("Running")
        for orbits in constellations:
            for orbit in orbits:
                for sat in orbit.satellites:
                    sat.refresh(CONST_SAT_DT)
        sleep(1.5)
        if running == True:
            break
    if orbit_cnt > 0:
        a = input("start orbit/sat number:(orbit index/sat index)")
        b = input("end orbit/sat number:(orbit index/sat index)")
        s_orbit, s_sat = int(a.split("/")[0]), int(a.split("/")[1])
        e_orbit, e_sat = int(b.split("/")[0]), int(b.split("/")[1])
        network.routing(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])
        # network.get_euc_distance(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])

        for i in range(len(network.log)):
            if len(network.log) > 1:
                for j in network.log[i-1]["path"]:
                    j.sat_attr.color = color.white
            for j in network.log[i]["path"]:
                j.sat_attr.color = color.cyan

        print("============log details============")
        print("packt_ID       delay(ms)         path")
        packet_idx = 0
        for i in network.log:
            print(packet_idx, "            ", i["delay"], "        ", end="[")
            for j in i["path"][:-1]:
                print(j.id, end="->")
            print(i["path"][-1].id + "]")
            packet_idx += 1
