'Python 3.9'
import time
import numpy as np
import vpython

'Web VPython 3.2'
from vpython import *
import pyautogui
import math
from minimum_deflection_angle import *
import threading

# 상수선언
orbitNum = 72
satNum = 22
maxDistance = 0
CONST_EARTH_RADIUS = 6371  # 지구반경
# CONST_ORBIT_RADIUS = CONST_EARTH_RADIUS + 550  # 지구반경 + 550KM
orbitRot = math.radians(360 / orbitNum)  # 궤도회전각도
satRot = math.radians(360 / satNum)  # 위성회전각도
CONST_SAT_DT = math.radians(5)  # 위성 공전 각도
v = vpython.color()
CONST_COLORS = [v.red, v.blue, v.green, v.white]


class Orbit:
    # 궤도 객체의 attribute
    id = "ORBIT-"
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
            # print(sat.id, "is appended in", self.id)
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
    state = None

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

        if math.degrees(theta) >= 270 or math.degrees(theta) <= 90:
            self.state = 'up'
        else:
            self.state = 'down'

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

        return [self.x, self.y, self.z]

    def get_sat_info(self):
        start_info = self.id.split("-")
        info = {"orbit": int(start_info[1]),
                "satellite": int(start_info[2]),
                }
        return info

    def refresh(self, dt):
        self.true_anomaly = math.radians((math.degrees(self.true_anomaly) + dt) % 360)
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
        true_anom_degree = math.degrees(self.true_anomaly)
        if true_anom_degree >= 270 or true_anom_degree <= 90:
            self.state = 'up'
        else:
            self.state = 'down'

    def get_great_distance(self, node_A, node_B):
        radius = CONST_EARTH_RADIUS + node_A.get_llh_info()['alt']
        lon_node_A = node_A.get_llh_info()['lon']
        lat_node_A = node_A.get_llh_info()['lat']
        lon_node_B = node_B.get_llh_info()['lon']
        lat_node_B = node_B.get_llh_info()['lat']

        lon_node_A = math.radians(lon_node_A)
        lat_node_A = math.radians(lat_node_A)
        lon_node_B = math.radians(lon_node_B)
        lat_node_B = math.radians(lat_node_B)

        dlon = lon_node_B - lon_node_A
        dlat = lat_node_B - lat_node_A

        a = math.sin(dlat / 2) ** 2 + math.cos(lat_node_A) * math.cos(lat_node_B) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c
        return distance

    def get_proper2(self, dest, available_list):
        smallest_distance = float('inf')
        index_of_point_with_smallest_distance = None
        print("current sat:", self.id)
        print("available list is")
        for i in range(len(available_list)):
            if available_list[i].id == dest.id:
                return i
            dist = self.get_great_distance(available_list[i], dest)
            print(available_list[i].id, "  distance:", dist)
            if dist < smallest_distance and dist > 100:
                smallest_distance = dist
                index_of_point_with_smallest_distance = i
        print("====================================")

        return index_of_point_with_smallest_distance

    def transfer(self, destination, path):
        print("packet is in", self.id)
        # sleep(1)
        path.append(self)
        if destination.id == self.id:
            return path
        else:
            dest_info = destination.get_ecef_info()
            cur_info = self.get_ecef_info()
            available_list = []
            available_list_ecef = []
            for orb in constellations[0]:
                for hop in orb.satellites:
                    # and (hop.orbit or self.state == hop.state) 인클 디클 고려 조건
                    if hop != self and max_dist_condition(cur_info, hop.get_ecef_info(), maxDistance):
                        available_list.append(hop)
                        available_list_ecef.append(hop.get_ecef_info())
            index_of_next_hop = self.get_proper2(destination, available_list)
            print("next hop is", available_list[index_of_next_hop].id)
            # sleep(1)
            return available_list[index_of_next_hop].transfer(destination, path)


class Network:
    def __init__(self):
        self.log = []

    # 유클리드 기반 노드 간 거리
    def get_euc_distance(self, node_A: Satellite, node_B: Satellite):
        node_A_ecef = node_A.get_ecef_info()
        node_B_ecef = node_B.get_ecef_info()
        print(node_B_ecef)
        return math.dist(node_A_ecef, node_B_ecef)

    # laser 기반 delay 계산
    def get_delay(self, node_A: Satellite, node_B: Satellite):
        distance = self.get_euc_distance(node_A, node_B)
        return distance / 3.0e8

    def routing(self, start: Satellite, dest: Satellite):
        path = start.transfer(dest, [])
        delay = self.get_delay(start, dest)
        self.log.append({
            "packet": "Packet-" + start.id + "To" + dest.id,
            "delay": round(delay * 1000, 6),
            "path": path,
        })


def get_perpendicular_vector(point_coordinates):
    point_coordinates = (point_coordinates.x, point_coordinates.y, point_coordinates.z)
    point_vector = np.array(point_coordinates, dtype=float)

    perpendicular_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    perpendicular_vector -= np.dot(perpendicular_vector, point_vector) / np.dot(point_vector,
                                                                                point_vector) * point_vector

    perpendicular_vector /= np.linalg.norm(perpendicular_vector)
    perpendicular_vector = vector(perpendicular_vector[0], perpendicular_vector[1], perpendicular_vector[2])
    return perpendicular_vector


def draw_max_distance_circle(node_position, max_distance):
    distance_circles.append(sphere(pos=node_position, radius=max_distance, color=color.green, opacity=0.1))


def refresh_max_distance_circle():
    for r in range(len(distance_circles)):
        distance_circles[r].pos = network.log[0]["path"][r].sat_attr.pos


def Inc(i):
    return i.number


def Alt(a):
    return a.number


def OrbNum(o):
    return o.number


def SatNum(s):
    return s.number


def MaxDist(d):
    return d.number


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


def Route(t):
    t.text = "Routing"
    network_simulator_thread.start()
    t.text = "Route"


def Src(q):
    return q.text


def Dst(d):
    return d.text


# 이중for문을 통하여 궤도 및 위성 배치 함수
def deploy(inc, axis, color):
    orbits = []
    if int(math.degrees(inc)) == 90:
        for i in range(int(orbitNum / 2)):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
    else:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
    constellations.append(orbits)


class RoutingSimulator:
    def __init__(self):
        self.network = Network()

    def simulate(self, src_count, dest_count):
        a = Src(q)
        b = Dst(d)
        s_orbit, s_sat = int(a.split("/")[0]), int(a.split("/")[1])
        e_orbit, e_sat = int(b.split("/")[0]), int(b.split("/")[1])
        self.network.routing(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])
        # network.get_euc_distance(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])

    def show_result_to_GUI(self):
        for i in range(len(self.network.log)):
            if len(self.network.log) > 1:
                for j in self.network.log[i - 1]["path"]:
                    j.sat_attr.color = color.white
                    j.sat_attr.radius = 60
                for j in distance_circles:
                    j.visible = False
            for j in self.network.log[i]["path"]:
                j.sat_attr.color = color.cyan
                j.sat_attr.radius = 120
                draw_max_distance_circle(j.sat_attr.pos, maxDistance)

    def reset_GUI(self):
        for i in range(len(network.log)):
            for j in network.log[i - 1]["path"]:
                j.sat_attr.color = color.white
                j.sat_attr.radius = 60
            for j in distance_circles:
                j.visible = False

    def print_log(self):
        print("============log details============")
        print("packt_ID       delay(ms)         path")
        packet_idx = 0
        for i in network.log:
            print(packet_idx, "            ", i["delay"], "        ", end="[")
            for j in i["path"][:-1]:
                print(j.id, end="->")
            print(i["path"][-1].id + "]")
            packet_idx += 1


# 클래스 끝, 메인 로직 시작

# 궤도 및 위성 리스트 생성
constellations = []
distance_circles = []

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
scene.caption = "\nOrbital inclination /  Altitude  / Orbits Number / Satellites Number / Max Transfer distance        /     Source     / Destination\n\n"

n = winput(bind=Inc, width=120, type="numeric")
i = winput(bind=Alt, width=120, type="numeric")
o = winput(bind=OrbNum, width=120, type="numeric")
s = winput(bind=SatNum, width=120, type="numeric")
m = winput(bind=MaxDist, width=120, type="numeric")
button(text="Set", bind=Set)
button(text="Run", bind=Run)
q = winput(bind=Src, width=120, type="string")
d = winput(bind=Dst, width=120, type="string")
button(text="Route", bind=Route)

# 메인
orbit_cnt = 0
network = Network()
network_simulator_thread = threading.Thread(target=routing_simulation)

while 1:

    while setting == False:
        # 케플러요소 입력
        # print("Setting")
        inclination = math.radians(float(Inc(n)))  # 궤도경사
        altitude = int(Alt(i))  # 궤도 반지름
        orbitNum = OrbNum(o)
        satNum = SatNum(s)
        orbitRot = math.radians(360 / orbitNum)
        satRot = math.radians(360 / satNum)
        maxDistance = MaxDist(m)
        deploy(inclination, altitude, CONST_COLORS[orbit_cnt])
        orbit_cnt = (orbit_cnt + 1) % 4
        setting = not setting

    while running == False:
        # print("Running")
        for orbits in constellations:
            for orbit in orbits:
                for sat in orbit.satellites:
                    sat.refresh(CONST_SAT_DT)
                    refresh_max_distance_circle()
        sleep(0.1)
        if running == True:
            break
