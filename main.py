'Python 3.9'
import sys
import time
import numpy as np
from tqdm import tqdm

from GroundStation import GroundStation
from KNBG import connect_sat_ground
from RTPG import *
from algorithmsWithGround import ddr_with_ground, dtdr_with_ground, opspf_with_ground
from laserISL import *
from util import *

from math import sqrt, dist
from parameter import *
# 라우팅 시뮬레이터 관련
from minimum_deflection_angle import *
import random
import threading
from algorithms import *


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
        self.orbit_index = index
        self.id = self.id + str(index)
        self.inclination = inclination
        self.lon_of_ascending = lon_of_ascending
        self.semi_major_axis = CONST_EARTH_RADIUS
        self.phasing_radian = radians(360 * (PHASING_PARAMETER / (orbitNum * satNum)) * index)
        # 위성 배치
        for idx in range(satNum):
            sat = Satellite(self, idx, inclination, altitude, (idx * satRot + self.phasing_radian) % (2 * pi))
            self.satellites.append(sat)

    def get_orbit_info(self):
        info = {
            "semi-major axis": self.semi_major_axis,
            "inclination": self.inclination,
            "longitude of the ascending node": self.lon_of_ascending
        }
        return info


class Satellite:

    def __init__(self, orbit: Orbit, sat_index, inclination, alt, theta):
        # self.failed_state = False
        self.link_state = [1, 1]
        self.handover_timer = [0, 0]
        self.fail_experiences = {0: [], 1: []}
        # laser inter satellite link
        self.link = {"up": None, "down": None, "left": None, "right": None, "ground": []}
        self.before_inter_sat_vec_arr = []
        self.should_notice_recovery = False
        self.sat_index = sat_index
        self.orbit_index = orbit.orbit_index
        self.inclination = inclination
        self.lon_of_ascending = orbit.lon_of_ascending
        self.id = "SAT-" + str(orbit.id[6:]) + "-" + str(sat_index)
        # self.orbit = orbit
        self.true_anomaly = theta
        self.altitude = alt
        # 위도, 경도
        self.latitude = asin(sin(inclination) * sin(theta))
        self.longitude = ((atan2(cos(inclination) * sin(theta),
                                 cos(theta))) % (2 * np.pi) + orbit.lon_of_ascending) % (2 * pi)
        # ECEF 좌표
        self.x, self.y, self.z = update_ECEF(orbit.inclination, self.true_anomaly, orbit.lon_of_ascending,
                                             self.altitude + CONST_EARTH_RADIUS)
        self.check_moving_state()

        self.p = self.orbit_index
        u = self.true_anomaly if self.true_anomaly >= pi / 2 else self.true_anomaly + (pi * 2)
        self.r = int((u - pi / 2) // DELTA_PI)

    def check_moving_state(self):
        # 상승/하강 상태
        if 0 not in self.link_state:
            if degrees(self.true_anomaly) >= 270 or degrees(self.true_anomaly) <= 90:
                # if self.state == 'down':
                #     self.had_pat = [False, False]
                self.state = 'up'
                self.sphere_attr.color = color.orange
            else:
                self.state = 'down'
                self.sphere_attr.color = color.cyan
        if len(self.link["ground"]) > 0:
            self.sphere_attr.color = color.purple
            self.sphere_attr.radius = 70
        else:
            self.sphere_attr.radius = 40

    def check_link_state(self):
        global pat_available
        global routing_table
        if pat_available:
            for i in range(2):
                if self.link_state[i] == 1:
                    # if self.protect_timer[i] == 0 and self.link_state[i] == 1:
                    element = self.link["left" if i == 0 else "right"]
                    current_vec = np.array([element.x - self.x, element.y - self.y, element.z - self.z])
                    before_vec = self.before_inter_sat_vec_arr[i]
                    angle_gap = calc_angle_between_vectors(current_vec, before_vec)
                    if angle_gap > TOLERABLE_ANGLE:
                        self.change_link_state(i)
                        self.handover_timer[i] += HANDOVER_TIME
                        if not (self.link_state[0] or self.link_state[1]):
                            self.sphere_attr.color = color.black

                        else:
                            self.sphere_attr.color = color.red
                        if (self.sat_index, self.orbit_index) not in pat_sat_array:
                            pat_sat_array.add((self.sat_index, self.orbit_index))
                        # if self.id == "SAT-0-0":
                        #     write_simulation_result(self, element, i, angle_gap, time, LASER_ANGLE_THRESHOLD, get_euc_distance([self.x, self.y, self.z], [element.x, element.y, element.z]))

                    else:
                        self.new_link(i)
        else:
            self.new_link(0)
            self.new_link(1)

    def change_link_state(self, index):
        if self.link_state[index]:
            self.link_state[index] = 0
        else:
            self.link_state[index] = 1

    def get_llh_info(self):
        info = {
            "SAT-ID": self.id,
            "lon": degrees(self.longitude),
            "lat": degrees(self.latitude),
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

    def new_link(self, index):
        re_PAT(self, self.link["left" if index == 0 else "right"], index)

    def refresh(self, dt):
        self.true_anomaly = radians((degrees(self.true_anomaly) + dt) % 360)
        # 위도, 경도
        delta_latitude = asin(sin(self.inclination) * sin(self.true_anomaly)) - self.latitude
        delta_longitude = (atan2(cos(self.inclination) * sin(self.true_anomaly), cos(
            self.true_anomaly))) % (2 * np.pi) + self.lon_of_ascending - self.longitude
        is_passing_zero = self.latitude
        self.latitude += delta_latitude
        self.longitude += delta_longitude
        self.longitude = self.longitude % (2 * np.pi)
        is_passing_zero *= self.latitude

        u = self.true_anomaly if self.true_anomaly >= pi / 2 else self.true_anomaly + (pi * 2)
        self.r = int((u - pi / 2) // DELTA_PI)

        # ECEF 좌표
        self.x, self.y, self.z = update_ECEF(self.inclination, self.true_anomaly, self.lon_of_ascending,
                                             self.altitude + CONST_EARTH_RADIUS)
        # self.x, self.y, self.z = update_ECEF(self.latitude, self.longitude, self.altitude + CONST_EARTH_RADIUS)
        # 3try
        # for i in range(len(self.link_sat)):
        #     # print("before azi:", self.laser_azimuth[i], "before ele:", self.laser_elevation[i], "before vec:", self.laser_vec[i])
        #     self.laser_elevation[i] += delta_latitude
        #     self.laser_azimuth[i] += delta_longitude
        #     self.laser_azimuth[i] = self.laser_azimuth[i] % (2*np.pi)
        #     x, y, z = update_ECEF(self.laser_elevation[i], self.laser_azimuth[i], np.linalg.norm(self.laser_vec[i]))
        #     self.laser_vec[i] = np.array([x, y, z])
        #     # print("after azi:", self.laser_azimuth[i], "after ele:", self.laser_elevation[i], "after vec:", self.laser_vec[i])
        # 구체 attribute 재설정
        # ###################################################gui
        # self.sphere_attr.pos = vec(self.y, self.z, self.x)
        # self.check_moving_state()
        #####################################################
        # self.distance.pos = self.sphere_attr.pos





class Packet:
    packet_count = 0

    def __init__(self, src: Satellite, dst: Satellite):
        self.index = Packet.packet_count
        Packet.packet_count += 1
        self.src = src
        self.dst = dst
        self.name = "[" + self.src.id + "->" + self.dst.id + "]"
        self.path = []
        self.overhead_signal = 0
        self.delay = 0
        self.fail_count = 0

    def transfer(self):
        global routing_table
        global detour_table
        # 최적 위성 탐색
        # self.path, self.fail_info = dijkstra(minimum_hop_region, s_sat, s_orbit, dst_sat, dst_orbit)
        if ALGORITHM == "DDR":
            self.path, self.fail_count, self.overhead_signal, detour_table = distributed_detour_routing(rtpg.graph,
                                                                                                        detour_table,
                                                                                                        self.src.p,
                                                                                                        self.src.r,
                                                                                                        self.dst.p,
                                                                                                        self.dst.r)
        elif ALGORITHM == "DTDR":
            self.path, self.fail_count, self.overhead_signal, detour_table = dtdr(rtpg.graph, detour_table, self.src.p,
                                                                                  self.src.r, self.dst.p, self.dst.r)
        elif ALGORITHM == "OPSPF":
            self.path, self.fail_count, routing_table, self.overhead_signal = opspf(constellation, routing_table, self.src.id, self.dst.id)
        elif ALGORITHM == "DDRwG":
            self.path, self.fail_count, self.overhead_signal, detour_table = ddr_with_ground(rtpg.graph, detour_table,
                                                                                                        self.src.p,
                                                                                                        self.src.r,
                                                                                                        self.dst.p,
                                                                                                        self.dst.r)
        elif ALGORITHM == "DTDRwG":
            self.path, self.fail_count, self.overhead_signal, detour_table = dtdr_with_ground(rtpg.graph, detour_table, self.src.p,
                                                                                  self.src.r, self.dst.p, self.dst.r)
        elif ALGORITHM == "OPSPFwG":
            self.path, self.fail_count, routing_table, self.overhead_signal = opspf_with_ground(constellation, routing_table, self.src.id, self.dst.id)


class Network:
    def __init__(self):
        self.log = []
        # self.fail_log = {}

    # 유클리드 기반 노드 간 거리
    def get_euc_distance(self, node_A: Satellite, node_B: Satellite):
        node_A_ecef = node_A.get_ecef_info()
        node_B_ecef = node_B.get_ecef_info()
        return dist(node_A_ecef, node_B_ecef)

    # laser 기반 delay 계산
    def get_delay(self, node_A: Satellite, node_B: Satellite):
        distance = self.get_euc_distance(node_A, node_B)
        # print(distance)
        return (distance / 3.0e5) * 1000

    def routing(self, start: Satellite, dest: Satellite):
        packet = Packet(start, dest)
        packet.transfer()
        a = packet.path[0]
        for b in packet.path[1:]:
            # print(a.id, "to", b.id, ":", self.get_delay(a, b))
            packet.delay += self.get_delay(a, b)
            # print("sum: ", packet.delay)
            a = b
        # if len(packet.fail_info) > 0:
        # self.fail_log[str(len(self.log))] = packet.fail_info
        self.log.append(packet)
        # TODO: fail_info 차원수 추가에 따른 수정 -> show GUI까지

        # self.fail_log[str(len(self.log))] = packet.fail_info
        # self.log.append({
        #     "index": len(self.log),
        #     "packet": "[" + start.id + " -> " + dest.id + "]",
        #     "delay": round(delay * 1000, 6),
        #     "path": path,
        # })

    def reset(self):
        self.log.clear()
        # self.fail_log.clear()


class RoutingSimulator:
    network = None
    worker = []
    randomSatList = []
    parallelProcess = []
    fail_objects = {}

    def __init__(self):
        self.network = Network()

    # def one_to_one(self):
    #     thread = threading.Thread(target=self.one_to_one_simulate)
    #     thread.start()
    #     # 종료까지 blocking
    #     thread.join()
    #     # 종료후 결과 표출
    #     self.print_log()

    # def one_to_one_simulate(self):
    #     a = Src(q)
    #     b = Dst(d)
    #     s_orbit, s_sat = int(a.split("/")[0]), int(a.split("/")[1])
    #     e_orbit, e_sat = int(b.split("/")[0]), int(b.split("/")[1])
    #     self.network.routing(constellations[0][s_orbit].satellites[s_sat], constellations[0][e_orbit].satellites[e_sat])

    def random_N_to_one_simulation(self, count):
        for i in range(int(count) + 1):
            random_orbit = np.random.randint(0, orbitNum)
            random_sat = np.random.randint(0, satNum)
            self.randomSatList.append(constellations[0][random_orbit].satellites[random_sat])
        random.shuffle(self.randomSatList)
        for k in range(int(count) + 1):  # 디버깅용
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
        for i in range(int(count) * 2):
            random_orbit = np.random.randint(0, orbitNum)
            random_sat = np.random.randint(0, satNum)
            self.randomSatList.append(constellations[0][random_orbit].satellites[random_sat])
        random.shuffle(self.randomSatList)
        # for k in range(int(count) * 2):  # 디버깅용
        #     print(self.randomSatList[k])

        for j in range(int(count)):
            sat1 = self.randomSatList[j]
            sat2 = self.randomSatList[int(count) + j]
            self.network.routing(sat1, sat2)

    def print_log(self):
        print("============log details============")
        print("packt_ID       delay(ms)         path")
        packet_idx = 0
        for i in self.network.log:
            print(packet_idx, "            ", i.delay, "        ", end="[")
            for j in i.path[:-1]:
                print(j.id, end="->")
            print(i.path[-1].id + "]")
            packet_idx += 1



# 이중for문을 통하여 궤도 및 위성 배치 함수
def deploy(inc, axis, color):
    orbits = []
    if int(degrees(inc)) >= 89:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, (orbitRot * i) / 2, color))
            rtpg.append_orbit(orbits[-1].satellites)
    else:
        for i in range(orbitNum):  # 궤도생성
            orbits.append(Orbit(i, inc, axis, orbitRot * i, color))
            rtpg.append_orbit(orbits[-1].satellites)
    constellations.append(orbits)
    initialize_lisl(constellations[-1])

    for g in ground_stations:
        g.connect_satellites(constellations[-1])


def deploy_starlink():
    inclination = radians(float(53))
    altitude = 550
    orbitNum = 22
    satNum = 72
    orbitRot = radians(360 / orbitNum)
    satRot = radians(360 / satNum)
    deploy(inclination, altitude, CONST_COLORS[0])


def routing_result_csv():
    write_routing_simulation_result(simulator.network.log, TOLERABLE_ANGLE_PER_SECOND)


# 클래스 끝, 메인 로직 시작

TOLERABLE_ANGLE_PER_SECOND = float(sys.argv[1])
ALGORITHM = sys.argv[2] #[1][0]
TOLERABLE_ANGLE = TOLERABLE_ANGLE_PER_SECOND * (SLOT_DURATION / 1000)
orbitNum = 72
satNum = 22
maxDistance = 0
inclination = radians(float(53))
orbitRot = radians(360 / orbitNum)  # 궤도회전각도
satRot = radians(360 / satNum)  # 위성회전각도
# 궤도 및 위성 리스트 생성
constellations = []
pat_sat_array = set()
protect_sat_array = []
ground_stations = []

#기지국
for g_info in GROUND_GEO_INFO:
    station = GroundStation(g_info, inclination)
    ground_stations.append(station)

# for g in ground_stations:
#     g.print_GS_info()
# print(G_SEARCH_REGION_RADIUS)

# 메인
time = 0
orbit_cnt = 0
simulator = RoutingSimulator()
rtpg = RTPG()
menu_choice = 0
veta_results = []
pat_available = True
# set_simulation_result(TOLERABLE_ANGLE_PER_SECOND)
# set_routing_simulation_result(TOLERABLE_ANGLE_PER_SECOND)
deploy_starlink()
constellation = []
detour_table = {}
routing_table = {}
for i in constellations[-1]:
    constellation.append(i.satellites)
    for j in i.satellites:
        detour_table[j.id] = set()
        routing_table[j.id] = [True, True]


# 타이머 & 핸드오버
for t in tqdm(range(0, SIMULATION_TIME + 1, SLOT_DURATION)):
    time = t
    to_discard = set()
    for (si, oi) in pat_sat_array:
        sat = constellation[oi][si]
        for index in range(2):
            if sat.handover_timer[index] > 0:
                sat.handover_timer[index] -= SLOT_DURATION
                if sat.handover_timer[index] <= 0:
                    sat.handover_timer[index] = 0
                    sat.change_link_state(index)
                    sat.new_link(index)
                    if ALGORITHM != "OPSPF" and ALGORITHM != "OPSF":
                        for fail_experience in sat.fail_experiences[index]:
                            detour_table = recovery_flood(sat, index, detour_table)
                        sat.fail_experiences[index].clear()
                    routing_table[sat.id][index] = True

                    # sat.protect_timer[index] += PROTECT_TIME
                    # if sat not in protect_sat_array:
                    #     protect_sat_array.append(sat)
                    # print(sat.handover_timer)
        if 0 not in sat.link_state:
            to_discard.add((si, oi))
    for i in to_discard:
        pat_sat_array.discard(i)

    # sleep(0.2)
    # 공전
    for orbits in constellations:
        for orbit in orbits:
            for sat in orbit.satellites:
                sat.refresh(CONST_SAT_DT)

    # 링크 확인
    for orbits in constellations:
        for orbit in orbits:
            for sat in orbit.satellites:
                sat.check_link_state()
    # 기지국
    # if time % 600 == 0:
    #     rtpg.refresh_rtpg()
    #     for g in ground_stations:
    #         g.reset_connections()
    #         g.connect_satellites(constellations[0])
    # if time % 100 == 0:
    #     simulator.random_N_to_M_simulation(50)
        # print(len(simulator.network.log))
    # if time % 40000 == 0:
    #     write_routing_simulation_result_partition(simulator.network.log, TOLERABLE_ANGLE_PER_SECOND, time/40000)
    #     simulator.network.reset()
    # if time % 80000 == 0:
    #     print(detour_table)
running = True
write_routing_simulation_result(ALGORITHM, simulator.network.log, TOLERABLE_ANGLE_PER_SECOND)


# 프로그램 종료
sys.exit(0)
# if running == True:
#     break
