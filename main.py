'Python 3.9'
import time
import numpy as np
import vpython
'Web VPython 3.2'
from vpython import *
import pyautogui
import math
# 라우팅 시뮬레이터 관련
from minimum_deflection_angle import *
import random
import threading
from algorithms import *
# 상수선언
SEOUL_LAT, SEOUL_LON = 37.56, 126.97
LA_LAT, LA_LON = 34.01, -118.41
orbitNum = 72
satNum = 22
maxDistance = 0
CONST_EARTH_RADIUS = 6371  # 지구반경
orbitRot = math.radians(360 / orbitNum)  # 궤도회전각도
satRot = math.radians(360 / satNum)  # 위성회전각도
CONST_SAT_DT = math.radians(15)  # 위성 공전 각도
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

    def get_orbit_info(self):
        info = {
            "semi-major axis": self.semi_major_axis,
            "inclination": self.inclination,
            "longitude of the ascending node": self.lon_of_ascending
        }
        return info


class Satellite:
    # 위성 객체의 attribute
    sphere_attr = None
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
    distance = None

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
        self.sphere_attr = sphere(pos=vec(self.y, self.z, self.x), axis=vec(0, 0, 1), radius=60, color=color.white)
        # 상승/하강 상태
        if math.degrees(theta) >= 270 or math.degrees(theta) <= 90:
            self.state = 'up'
        else:
            self.state = 'down'
        self.distance = sphere(pos=self.sphere_attr.pos, radius=maxDistance, color=color.green, opacity=0.1, visible=False)

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
        self.sphere_attr.pos = vec(self.y, self.z, self.x)
        true_anom_degree = math.degrees(self.true_anomaly)
        if true_anom_degree >= 270 or true_anom_degree <= 90:
            self.state = 'up'
        else:
            self.state = 'down'
        self.distance.pos = self.sphere_attr.pos

    def get_great_distance(self, node_B):
        lon_node_A = self.get_llh_info()['lon']
        lat_node_A = self.get_llh_info()['lat']
        lon_node_B = node_B.get_llh_info()['lon']
        lat_node_B = node_B.get_llh_info()['lat']

        return get_distance_with_lon_and_lat(lon_node_A, lat_node_A, lon_node_B, lat_node_B)

    def transfer(self, destination, path):
        path.append(self)
        if destination.id == self.id:
            return path
        else:
            cur_info = self.get_ecef_info()
            available_list = []
            available_list_ecef = []
            # 통신 가능 위성 취합 => available list
            for orb in constellations[0]:
                for hop in orb.satellites:
                    # and (hop.orbit or self.state == hop.state) 인클 디클 고려 조건
                    # if hop != self and max_dist_condition(cur_info, hop.get_ecef_info(), maxDistance):
                    if hop != self:
                        available_list.append(hop)
                        available_list_ecef.append(hop.get_ecef_info())
            # 최적 위성 탐색
            # next_hop = MDD(self, destination, available_list)
            # next_hop = MDA(self, destination, available_list)
            next_hop = TEW(self, self.get_sat_info(), destination.get_sat_info(), orbitNum, satNum)

            return next_hop.transfer(destination, path)


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


class RoutingSimulator:
    network = None
    worker = []
    randomSatList = []
    parallelProcess = []

    def __init__(self):
        self.network = Network()

    def one_to_one(self):
        thread = threading.Thread(target=self.one_to_one_simulate)
        thread.start()
        # 종료까지 blocking
        thread.join()
        # 종료후 결과 표출
        self.print_log()

    def one_to_one_simulate(self):
        a = Src(q)
        b = Dst(d)
        s_orbit, s_sat = int(a.split("/")[0]), int(a.split("/")[1])
        e_orbit, e_sat = int(b.split("/")[0]), int(b.split("/")[1])
        self.network.routing(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])

    def random_N_to_one_simulation(self, count):
        for i in range(int(count) + 1):
            random_orbit = np.random.randint(0, orbitNum)
            random_sat = np.random.randint(0, satNum)
            self.randomSatList.append(constellations[0][random_orbit].satellites[random_sat])
        random.shuffle(self.randomSatList)
        for k in range(int(count) + 1):#디버깅용
            print(self.randomSatList[k])
        for j in range(int(count)):  # 다중 라우팅 병렬처리
            self.parallelProcess.append(
                threading.Thread(target=self.network.routing(self.randomSatList[j], self.randomSatList[int(count)])))
            self.parallelProcess[j].start()  # 리스트 맨 마지막 위성으로 하나의 목적지 지정
        for i in self.parallelProcess:
            i.join()
        self.parallelProcess.clear()
        self.print_log()

    def random_N_to_M_simulation(self, count):
        for i in range(int(count)*2):
            random_orbit = np.random.randint(0, orbitNum)
            random_sat = np.random.randint(0, satNum)
            self.randomSatList.append(constellations[0][random_orbit].satellites[random_sat])
        random.shuffle(self.randomSatList)
        for k in range(int(count)*2): #디버깅용
            print(self.randomSatList[k])
        for j in range(int(count)): #다중 라우팅 병렬처리
            self.parallelProcess.append(threading.Thread(target=self.network.routing(self.randomSatList[j],self.randomSatList[int(count)+j])))
            self.parallelProcess[j].start() #리스트 맨 마지막 위성으로 하나의 목적지 지정
        self.parallelProcess.clear()
        self.print_log()

    def ground_to_ground_simulation(self, s_lon, s_lat, d_lon, d_lat):
        if s_lon < 0:
            s_lon += 360
        if d_lon < 0:
            d_lon += 360
        start = get_nearest_sat(s_lon, s_lat, constellations)
        end = get_nearest_sat(d_lon, d_lat, constellations)
        simulator.network.routing(start, end)
        veta_results.append(self.network.log[-1]["packet"])
        self.print_log()
        return 0

    def show_result_to_GUI(self, index):
        for i in range(len(self.network.log)):
            for j in self.network.log[i]["path"]:
                j.sphere_attr.color = color.white
                j.sphere_attr.radius = 60
                j.distance.visible = False
        for i in self.network.log[index]["path"]:
            if self.network.log[index]["path"].index(i) == 0:
                i.sphere_attr.color = color.orange
            elif self.network.log[index]["path"].index(i) == len(self.network.log[index]["path"])-1:
                i.sphere_attr.color = color.purple
            else:
                i.sphere_attr.color = color.cyan
            i.sphere_attr.radius = 120
            i.distance.visible = True

    def reset_GUI(self):
        for i in range(len(self.network.log)):
            for j in self.network.log[i]["path"]:
                j.sphere_attr.color = color.white
                j.sphere_attr.radius = 60
                j.distance.visible = False

    def print_log(self):
        print("============log details============")
        print("packt_ID       delay(ms)         path")
        packet_idx = 0
        for i in self.network.log:
            print(packet_idx, "            ", i["delay"], "        ", end="[")
            for j in i["path"][:-1]:
                print(j.id, end="->")
            print(i["path"][-1].id + "]")
            packet_idx += 1


def get_perpendicular_vector(point_coordinates):
    point_coordinates = (point_coordinates.x, point_coordinates.y, point_coordinates.z)
    point_vector = np.array(point_coordinates, dtype=float)

    perpendicular_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    perpendicular_vector -= np.dot(perpendicular_vector, point_vector) / np.dot(point_vector,
                                                                                point_vector) * point_vector

    perpendicular_vector /= np.linalg.norm(perpendicular_vector)
    perpendicular_vector = vector(perpendicular_vector[0], perpendicular_vector[1], perpendicular_vector[2])
    return perpendicular_vector


def func_visible(r):
    if r.checked:
        for i in simulator.network.log[menu_choice]["path"]:
            i.distance.opacity = 0.1
    else:
        for i in simulator.network.log[menu_choice]["path"]:
            i.distance.opacity = 0

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
    simulator.random_N_to_M_simulation(Count(cont))
    t.text = "Route"
    log_list = ["None"]
    for i in simulator.network.log:
        log_list.append(i["packet"]+" (delay: "+str(i["delay"])+")")
    routing_list_menu.choices = log_list

def seoul_to_la(t):
    t.text = "Routing"
    simulator.ground_to_ground_simulation(SEOUL_LON, SEOUL_LAT, LA_LON, LA_LAT)
    t.text = "Seoul -> LA (veta)"
    log_list = routing_list_menu.choices
    log_list.append("[veta] SEOUL to LA")
    routing_list_menu.choices = log_list

def Src(q):
    return q.text


def Dst(d):
    return d.text


def Count(c):
    return c.text


def Mto1(cont):
    return cont.text


def chooseLog(m):
    global menu_choice
    print(m.selected)
    if m.selected is None:
        simulator.reset_GUI()
    else:
        for i in range(len(routing_list_menu.choices[1:])):
            if m.selected == routing_list_menu.choices[i+1]:
                menu_choice = i
                break
        print(menu_choice)
        simulator.show_result_to_GUI(menu_choice)


# 이중for문을 통하여 궤도 및 위성 배치 함수
def deploy(inc, axis, color):
    orbits = []
    if int(math.degrees(inc)) == 90:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, (orbitRot * i)/2, color))
    else:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
    constellations.append(orbits)


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
scene.caption = "\nOrbital inclination /  Altitude  / Orbits Number / Satellites Number / Max Transfer distance      Number of paths\n\n"
# "\nOrbital inclination /  Altitude  / Orbits Number / Satellites Number / Max Transfer distance        /     Source     / Destination\n\n"

n = winput(bind=Inc, width=120, type="numeric")
i = winput(bind=Alt, width=120, type="numeric")
o = winput(bind=OrbNum, width=120, type="numeric")
s = winput(bind=SatNum, width=120, type="numeric")
m = winput(bind=MaxDist, width=120, type="numeric")
button(text="Set", bind=Set)
button(text="Run", bind=Run)
# q = winput(bind=Src, width=120, type="string") # 1 to 1 용 변수
# d = winput(bind=Dst, width=120, type="string")
cont = winput(bind=Mto1, width=120, type="numeric")
button(text="Route", bind=Route)
button(text="Seoul -> LA (veta)", bind=seoul_to_la)
scene.append_to_caption("\n\n Routing result list  :  ")
routing_list_menu = menu(choices=["None"], index=0, bind=chooseLog)
scene.append_to_caption("\n\n connection visible")
checkbox(bind=func_visible, checked=True) # text to right of checkbox


# 메인
orbit_cnt = 0
simulator = RoutingSimulator()
menu_choice = 0
veta_results = []
seoul = sphere(pos=vec(math.cos(math.radians(37.5)) * math.sin(math.radians(127)) * (CONST_EARTH_RADIUS),
                       math.sin(math.radians(37.5)) * (CONST_EARTH_RADIUS),
                       math.cos(math.radians(37.5)) * math.cos(math.radians(127)) * (CONST_EARTH_RADIUS)), axis=vec(0, 0, 1), radius=60, color=color.red)
losangeles = sphere(pos=vec(math.cos(math.radians(34)) * math.sin(math.radians(-118)) * (CONST_EARTH_RADIUS),
                       math.sin(math.radians(34)) * (CONST_EARTH_RADIUS),
                       math.cos(math.radians(34)) * math.cos(math.radians(-118)) * (CONST_EARTH_RADIUS)), axis=vec(0, 0, 1), radius=60, color=color.red)
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
        for i in range(len(simulator.network.log)):
            path = simulator.network.log[i]["path"]
            if simulator.network.log[i]["packet"] in veta_results:
                first_sat_llh = path[0].get_llh_info()
                last_sat_llh = path[-1].get_llh_info()
                print(first_sat_llh)
                print(last_sat_llh)
                seoul_to_first_sat = get_distance_with_lon_and_lat(SEOUL_LON, SEOUL_LAT,
                                                                   first_sat_llh["lon"], first_sat_llh["lat"])
                la_to_last_sat = get_distance_with_lon_and_lat(LA_LON, LA_LAT,
                                                               last_sat_llh["lon"], last_sat_llh["lat"])
                print(seoul_to_first_sat, la_to_last_sat)
                # if seoul_to_first_sat > maxDistance or la_to_last_sat > maxDistance:
                if get_nearest_sat(SEOUL_LON, SEOUL_LAT, constellations) != path[0] or get_nearest_sat(LA_LON, LA_LAT, constellations) != path[-1]:
                    simulator.ground_to_ground_simulation(SEOUL_LON, SEOUL_LAT, LA_LON, LA_LAT)
                    veta_results.remove(simulator.network.log[i]["packet"])
                    if menu_choice == i:
                        simulator.reset_GUI()
                    simulator.network.log[i] = simulator.network.log[-1]
                    simulator.network.log.pop()
                    print(veta_results)
                    print(veta_results)
                    if menu_choice == i:
                        simulator.show_result_to_GUI(i)
                    # simulator.network.log.pop()
                    break
                else:
                    before = path[0]
                    for current in path[1:]:
                        if current.get_great_distance(before) > maxDistance:
                            print("punk!(", current.get_great_distance(before),")")
                            print("before:", before.id, "current:", current.id)
                            simulator.ground_to_ground_simulation(SEOUL_LON, SEOUL_LAT, LA_LON, LA_LAT)
                            veta_results.remove(simulator.network.log[i]["packet"])
                            if menu_choice == i:
                                simulator.reset_GUI()
                            simulator.network.log[i] = simulator.network.log[-1]
                            simulator.network.log.pop()
                            print(veta_results)
                            print(veta_results)
                            if menu_choice == i:
                                simulator.show_result_to_GUI(i)
                            # simulator.network.log.pop()
                            break
                        before = current
            else:
                before = path[0]
                for current in path[1:]:
                    if current.get_great_distance(before) > maxDistance:
                        simulator.network.routing(path[0], path[-1])
                        if menu_choice == i:
                            simulator.reset_GUI()
                        simulator.network.log[i] = simulator.network.log[-1]
                        simulator.network.log.pop()
                        new_list = ["None"]
                        for j in simulator.network.log:
                            new_list.append(j["packet"] + " (delay: " + str(j["delay"]) + ")")
                        routing_list_menu.choices = new_list
                        if menu_choice == i:
                            simulator.show_result_to_GUI(i)
                        break
                    before = current
        sleep(0.5)
        if running == True:
            break

