'Python 3.9'
import concurrent.futures
import sys
import time
import numpy as np
import vpython
from tqdm import tqdm
from KNBG import connect_sat_ground
from RTPG import *
from laserISL import *
from util import *

'Web VPython 3.2'
from vpython import *
import pyautogui
import math
from parameter import *
# 라우팅 시뮬레이터 관련
from minimum_deflection_angle import *
import random
import threading
from algorithms import *
import detourTable



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
        self.phasing_radian = radians(360*(PHASING_PARAMETER / (orbitNum*satNum)) * index)
        # 궤도 회전 -1을 넣은 이유는 45~47번 코드를 주석해제해서 실행시켜보면 궤도가 xz평면기준으로 반대로 되어있었음을 알 수 있음
        self.orbit_attr = ring(pos=vec(0, 0, 0), opacity=0.15,
                               axis=vec(-1 * sin(inclination) * cos(lon_of_ascending),
                                        cos(inclination),
                                        sin(lon_of_ascending) * sin(inclination)),
                               color=color, thickness=15, radius=self.semi_major_axis + altitude, )
        # 위성 배치
        for idx in range(satNum):
            sat = Satellite(self, idx, inclination, altitude, (idx * satRot + self.phasing_radian) % (2*pi))
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
                                     cos(theta))) % (2 * np.pi) + orbit.lon_of_ascending) % (2*pi)
        # ECEF 좌표
        self.x, self.y, self.z = update_ECEF(orbit.inclination, self.true_anomaly, orbit.lon_of_ascending, self.altitude + CONST_EARTH_RADIUS)
        # 구체 attribute 설정
        self.sphere_attr = sphere(pos=vec(self.y, self.z, self.x), radius=40, color=color.white, up=vec(100, 100, 100))
        # self.distance = sphere(pos=self.sphere_attr.pos, radius=maxDistance, color=color.green, opacity=0.1, visible=False)
        self.check_moving_state()

        self.p = self.orbit_index
        u = self.true_anomaly if self.true_anomaly >= pi/2 else self.true_anomaly+(pi*2)
        self.r = int((u - pi/2)//DELTA_PI)

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
        re_PAT(self, self.link["left" if index==0 else "right"], index)

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

        u = self.true_anomaly if self.true_anomaly >= pi/2 else self.true_anomaly+(pi*2)
        self.r = int((u - pi/2)//DELTA_PI)

        # ECEF 좌표
        self.x, self.y, self.z = update_ECEF(self.inclination, self.true_anomaly, self.lon_of_ascending, self.altitude + CONST_EARTH_RADIUS)
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


class GroundStation:
    id = 0
    def __init__(self, geo_info):
        self.id = GroundStation.id
        GroundStation.id += 1

        self.latitude = radians(geo_info[0])
        self.longitude = radians(geo_info[1])
        self.x, self.y, self.z = update_ECEF_using_lat_lon(self.latitude, self.longitude, CONST_EARTH_RADIUS)
        self.p_asc, self.r_asc, self.p_desc, self.r_desc = coordinates_of_ground_station(self.latitude, self.longitude, inclination)
        self.sphere_attr = sphere(pos=vec(self.y, self.z, self.x), radius=80, color=color.white, up=vec(100, 100, 100))
        self.delta_p, self.delta_r = grid_search_region(self.latitude, self.longitude, inclination)
        self.search_range_asc, self.search_range_desc = self.update_search_range()
        self.name = f'GS|a{self.p_asc}-{self.r_asc}|d{self.p_desc}-{self.r_desc}'
        self.connection_area = sphere(pos=vec(self.y, self.z, self.x), radius=G_SEARCH_REGION_RADIUS, color=color.green, up=vec(100, 100, 100), opacity=0.08)
        self.connections = []

        self.routing_table = {}

    def print_GS_info(self):
        print("=========")
        print("name:", self.name)
        print("latitude:", degrees(self.latitude))
        print("longitude:", degrees(self.longitude))
        print("p and r (asc):", self.p_asc, self.r_asc)
        print("p and r (desc):", self.p_desc, self.r_desc)
        print("delta_p:", self.delta_p)
        print("delta_r:", self.delta_r)
        print("connection:", len(self.connections))

    def connect_satellites(self, constellation):
        # print("ground_station:", self.name)
        [horizontal_range_asc, vertical_range_asc] = self.search_range_asc
        [horizontal_range_desc, vertical_range_desc] = self.search_range_desc
        for p in (horizontal_range_asc+horizontal_range_desc):
            for sat in constellation[p].satellites:
                radius = calculate_distance_s_to_g(self.latitude, self.longitude, sat.latitude, sat.longitude)
                # print(elevation)
                if radius <= G_SEARCH_REGION_RADIUS:
                    # print(radius)
                    if self not in sat.link["ground"]:
                        sat.link["ground"].append(self)
                    if sat not in self.connections:
                        self.connections.append(sat)
                    # ground station link attr
                    # sat.sphere_attr.radius = 70
                    # sat.sphere_attr.color = color.red

    def reset_connections(self):
        for sat in self.connections:
            sat.link["ground"].remove(self)

        self.connections = []


    def update_search_range(self):
        search_area_asc, search_area_desc = [], []
        area_left_bound_asc, area_left_bound_desc = int((self.p_asc - self.delta_p/2 + O_NUM) % O_NUM), int((self.p_desc - self.delta_p/2 + O_NUM) % O_NUM)
        area_right_bound_asc, area_right_bound_desc = int((self.p_asc + self.delta_p/2) % O_NUM), int((self.p_desc + self.delta_p/2) % O_NUM)
        area_upper_bound_asc, area_upper_bound_desc = int((self.r_asc + self.delta_r/2) % S_NUM), int((self.r_desc + self.delta_r/2) % S_NUM)
        area_lower_bound_asc, area_lower_bound_desc = int((self.r_asc - self.delta_r/2 + S_NUM) % S_NUM), int((self.r_desc - self.delta_r/2 + S_NUM) % S_NUM)

        if area_left_bound_asc < area_right_bound_asc:
            search_area_asc.append(list(range(area_left_bound_asc, area_right_bound_asc+1)))
        else:
            search_area_asc.append(list(range(area_left_bound_asc, O_NUM))+list(range(0, area_right_bound_asc+1)))
        if area_left_bound_desc < area_right_bound_desc:
            search_area_desc.append(list(range(area_left_bound_desc, area_right_bound_desc+1)))
        else:
            search_area_desc.append(list(range(area_right_bound_desc, O_NUM))+list(range(0, area_right_bound_desc+1)))

        if area_upper_bound_asc > area_lower_bound_asc:
            search_area_asc.append(list(range(area_lower_bound_asc, area_upper_bound_asc+1)))
        else:
            search_area_asc.append(list(range(area_upper_bound_asc, S_NUM))+list(range(0, area_lower_bound_asc+1)))
        if area_upper_bound_desc > area_lower_bound_desc:
            search_area_desc.append(list(range(area_lower_bound_desc, area_upper_bound_desc+1)))
        else:
            search_area_desc.append(list(range(area_upper_bound_desc, S_NUM))+list(range(0, area_lower_bound_desc+1)))

        return search_area_asc, search_area_desc


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
        if ALGORITHM == "OPSF" or ALGORITHM == "OPSPF":
            region, s_sat, s_orbit, dst_sat, dst_orbit = constellation_to_array(rtpg.graph), self.src.r, self.src.p, self.dst.r, self.dst.p
        # else:
            # minimum_hop_region, s_sat, s_orbit, dst_sat, dst_orbit = get_minimum_hop_region(self.src, self.dst, orbitNum,satNum, constellations[0])
            # mhr, s_sat, s_orbit, dst_sat, dst_orbit = new_mhr(self.src, self.dst, constellations[0])
        # self.path, self.fail_info = dijkstra(minimum_hop_region, s_sat, s_orbit, dst_sat, dst_orbit)
        # self.path, self.fail_info, self.overhead_signal = distributed_detour_routing(constellations[0], mhr, s_sat, s_orbit, dst_sat, dst_orbit, self.src, self.dst)
        self.path, self.fail_count, self.overhead_signal, detour_table = dtdr(detour_table, self.src, self.dst)
        # self.path, self.fail_info, routing_table, self.overhead_signal = opspf(region, routing_table, s_sat, s_orbit, dst_sat, dst_orbit)


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
        return (distance / 3.0e5)*1000

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


    # def ground_to_ground_simulation(self):
    #     src, dst = ground_Src(ground_src), ground_Dst(ground_dst)
    #     s_lon, s_lat = CITY_INFO[src]
    #     d_lon, d_lat = CITY_INFO[dst]
    #     if s_lon < 0:
    #         s_lon += 360
    #     if d_lon < 0:
    #         d_lon += 360
    #     start = get_nearest_sat(s_lon, s_lat, constellations)
    #     end = get_nearest_sat(d_lon, d_lat, constellations)
    #     simulator.network.routing(start, end)
    #     self.print_log()
    #     return 0

    # def show_result_to_GUI(self, index):
    #     vector_list = []
    #     packet_line_list = []
    #     fail_point = None
    #     fail_line = None
    #
    #     for i in range(len(self.network.log)):
    #         for j in self.network.log[i].path:
    #             j.sphere_attr.color = color.white
    #             j.sphere_attr.radius = 60
    #             # j.distance.visible = False
    #
    #     for i in self.network.log[index].path:
    #         if self.network.log[index].path.index(i) == 0:
    #             i.sphere_attr.color = color.orange
    #         elif self.network.log[index].path.index(i) == len(self.network.log[index].path) - 1:
    #             i.sphere_attr.color = color.purple
    #         # elif i.failed_state == True:
    #         #     i.sphere_attr.color = color.red
    #         else:
    #             i.sphere_attr.color = color.cyan
    #         i.sphere_attr.radius = 120
    #
    #     # vec list appending
    #     for i in self.network.log[index].path:
    #         vector_list.append(vec(i.get_ecef_info()[1], i.get_ecef_info()[2], i.get_ecef_info()[0]))
    #
    #     # packet line appending / lining
    #     for i in range(len(vector_list) - 1):
    #         line = arrow(pos=vector_list[i], axis=vector_list[i + 1] - vector_list[i], shaftwidth=50, headwidth=200,
    #                      headlength=200,
    #                      length=mag(vector_list[i + 1] - vector_list[i]),
    #                      color=color.green, opacity=1)
    #         packet_line_list.append(line)
    #
    #     # failure pointing & lining
    #     print(str(index), self.network.fail_log)
    #     if len(self.network.fail_log[str(index)]):
    #         if str(index) in RoutingSimulator.fail_objects:
    #             for fail_obj in RoutingSimulator.fail_objects[str(index)]:
    #                 fail_obj.opacity = 1
    #         else:
    #             fail_arr = []
    #             for fail_pair in self.network.fail_log[str(index)]:
    #                 fail_sat1 = fail_pair[0]
    #                 fail_sat2 = fail_pair[1]
    #                 fail_sat1_info = vec(fail_sat1.get_ecef_info()[1], fail_sat1.get_ecef_info()[2],
    #                                      fail_sat1.get_ecef_info()[0])
    #                 fail_sat2_info = vec(fail_sat2.get_ecef_info()[1], fail_sat2.get_ecef_info()[2],
    #                                      fail_sat2.get_ecef_info()[0])
    #                 fail_point = vp.sphere(pos=fail_sat1_info, radius=150, color=color.red, opacity=1)
    #                 fail_line = arrow(pos=fail_sat1_info, axis=fail_sat2_info - fail_sat1_info, shaftwidth=50,
    #                                   headwidth=0,
    #                                   headlength=0,
    #                                   length=mag(fail_sat2_info - fail_sat1_info),
    #                                   color=color.red, opacity=1)
    #                 fail_arr.append(fail_point)
    #                 fail_arr.append(fail_line)
    #             RoutingSimulator.fail_objects[str(index)] = fail_arr
    #
    #     # moving dot moving
    #     moving_dot = vp.sphere(pos=vector_list[0], radius=200, color=color.green, opacity=1)
    #     dt = 0.01
    #     for i in range(len(vector_list) - 1):
    #         t = 0.0
    #         while t <= 1.0:
    #             rate(300)
    #             moving_dot.pos = vector_list[i] + t * (vector_list[i + 1] - vector_list[i])
    #             t += dt
    #
    #     # packet line hiding
    #     for i in range(len(vector_list) - 1):
    #         packet_line_list[i].opacity = 0
    #
    #     # moving dot hiding
    #     moving_dot.opacity = 0
    #
    #     if len(self.network.fail_log[str(index)]):
    #         for fail_obj in RoutingSimulator.fail_objects[str(index)]:
    #             fail_obj.opacity = 0

    def reset_GUI(self):
        for i in range(len(self.network.log)):
            for j in self.network.log[i].path:
                j.sphere_attr.color = color.orange if j.state == 'up' else color.cyan
                j.sphere_attr.radius = 40
            if str(i) in RoutingSimulator.fail_objects:
                for fail_obj in RoutingSimulator.fail_objects[str(i)]:
                    fail_obj.opacity = 1

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


def get_perpendicular_vector(point_coordinates):
    point_coordinates = (point_coordinates.x, point_coordinates.y, point_coordinates.z)
    point_vector = np.array(point_coordinates, dtype=float)

    perpendicular_vector = np.array([1.0, 0.0, 0.0], dtype=float)

    perpendicular_vector -= np.dot(perpendicular_vector, point_vector) / np.dot(point_vector,
                                                                                point_vector) * point_vector

    perpendicular_vector /= np.linalg.norm(perpendicular_vector)
    perpendicular_vector = vector(perpendicular_vector[0], perpendicular_vector[1], perpendicular_vector[2])
    return perpendicular_vector


def enable_PAT(r):
    global pat_available
    if r.checked:
        pat_available = True
    else:
        pat_available = False


def Inc(i):
    return i.number


def Alt(a):
    return a.number


def OrbNum(o):
    return o.number


def SatNum(s):
    return s.number


# def MaxDist(d):
#     return d.number


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


# def Route(t):
#     t.text = "Routing"
#     # simulator.random_N_to_M_simulation(Count(cont))
#     simulator.one_to_one()
#     t.text = "Route"
#     log_list = ["None"]
#     for i in simulator.network.log:
#         log_list.append(str(i.index) + ". " + i.name + " (delay: " + str(i.delay) + ")")
#     routing_list_menu.choices = log_list
#
#
# def ground(t):
#     t.text = "Routing"
#     simulator.ground_to_ground_simulation()
#     log_list = ["None"]
#     for i in simulator.network.log:
#         log_list.append(str(i.index) + ". " + i.name + " (delay: " + str(i.delay) + ")")
#     routing_list_menu.choices = log_list


# def reset_detour_table(t):
#     t.text = "Ing.."
#     for orbit in constellations[0]:
#         for sat in orbit.satellites:
#             sat.detourTable.clear()
#     t.text = "Reset detour tables"


def Src(q):
    return q.text


def Dst(d):
    return d.text

def ground_Src(g_src):
    return g_src.text

def ground_Dst(g_dst):
    return g_dst.text


def Count(c):
    return c.text


def Mto1(cont):
    return cont.text


# def chooseLog(m):
#     global menu_choice
#     print(m.selected)
#     if m.selected is None:
#         simulator.reset_GUI()
#     else:
#         for i in range(len(routing_list_menu.choices[1:])):
#             if m.selected == routing_list_menu.choices[i + 1]:
#                 menu_choice = i
#                 break
#         print(menu_choice)
#         simulator.show_result_to_GUI(menu_choice)


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
    # for s in constellations[-1][-1].satellites:
    #     print(s.id, s.link_sat[0].id, s.link_sat[1].id)
    #     s.sphere_attr.color = vpython.color.black
    #     s.link["left"].sphere_attr.color = vpython.color.green
    #     s.link["right"].sphere_attr.color = vpython.color.red
    for g in ground_stations:
        g.connect_satellites(constellations[-1])
    # ground_stations[0].connect_satellites(constellations[-1])
    # ground_stations[0].print_GS_info()




def deploy_starlink():
    inclination = radians(float(53))
    altitude = 550
    orbitNum = 22
    satNum = 72
    orbitRot = radians(360 / orbitNum)
    satRot = radians(360 / satNum)
    deploy(inclination, altitude, CONST_COLORS[0])
    # for o in constellations[0]:
    #     s = o.satellites[0]
    #     print(s.id, s.p, s.r, s.longitude, s.latitude, degrees(s.longitude), degrees(s.latitude))

    # print("=======================")
    # test_src, test_dst = constellations[-1][0].satellites[0], constellations[-1][3].satellites[3]
    # print(minimum_hop_estimate(test_src, test_dst))
    # test_src.sphere_attr.color = vpython.color.green
    # test_dst.sphere_attr.color = vpython.color.red
    # for g in ground_stations:
    #     g.print_GS_info()


def routing_result_csv():
    write_routing_simulation_result(simulator.network.log, TOLERABLE_ANGLE_PER_SECOND)

# 클래스 끝, 메인 로직 시작
# if __name__=="__main__":
TOLERABLE_ANGLE_PER_SECOND = float(sys.argv[1:][0])
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
routing_table = []
ground_stations = []

# 모니터 해상도에 따라 능동적인 해상도 조절
M_size = pyautogui.size()
monitor_width = M_size[0]
monitor_height = M_size[1] - 300

# 씬 구성
# 기준 춘분점(Reference direction vector = (0, 0, 1))
scene = canvas(width=monitor_width - 15, height=monitor_height - 15)
scene.resizable = False

earth = sphere(pos=vec(0, 0, 0), radius=CONST_EARTH_RADIUS, texture=textures.earth)  # 지구생성
#기지국
# for g_info in GROUND_GEO_INFO:
#     station = GroundStation(g_info)
#     ground_stations.append(station)

# for g in ground_stations:
#     g.print_GS_info()
# print(G_SEARCH_REGION_RADIUS)

# 입력 GUI구성
running = False
setting = True
# scene.caption = "\n                    Orbital inclination /  Altitude      / Orbits Number / Satellites Number             /     Source(sat)       / Destination(sat)\n\n"
# button(text="Starlink Phase1", bind=deploy_starlink)
# n = winput(bind=Inc, width=120, type="numeric")
# i = winput(bind=Alt, width=120, type="numeric")
# o = winput(bind=OrbNum, width=120, type="numeric")
# s = winput(bind=SatNum, width=120, type="numeric")
# # m = winput(bind=MaxDist, width=120, type="numeric")
# button(text="Set", bind=Set)
# button(text="Run", bind=Run)
# q = winput(bind=Src, width=120, type="string")  # 1 to 1 용 변수
# d = winput(bind=Dst, width=120, type="string")
# # cont = winput(bind=Mto1, width=120, type="numeric") # 멀티패스 입력란
# button(text="Route", bind=Route)
# # button(text="Seoul -> LA (veta)", bind=seoul_to_la)
# button(text="Reset detour tables", bind=reset_detour_table)
# scene.append_to_caption("\n\n ground to ground routing")
# ground_src = winput(bind=Src, width=120, type="string")  # 1 to 1 용 변수
# ground_dst = winput(bind=Dst, width=120, type="string")
# # cont = winput(bind=Mto1, width=120, type="numeric") # 멀티패스 입력란
# button(text="ground Route", bind=ground)
# scene.append_to_caption("\n\n Routing result list  :  ")
# routing_list_menu = menu(choices=["None"], index=0, bind=chooseLog)
# scene.append_to_caption("\n\n enable PAT")
# checkbox(bind=enable_PAT, checked=True)  # text to right of checkbox
# button(text="extract to csv", bind=routing_result_csv)
# 메인
time = 0
orbit_cnt = 0
simulator = RoutingSimulator()
rtpg = RTPG()
menu_choice = 0
veta_results = []
pat_available = True
# set_simulation_result(TOLERABLE_ANGLE_PER_SECOND)
set_routing_simulation_result(TOLERABLE_ANGLE_PER_SECOND)
deploy_starlink()
constellation = []
detour_table = {}
for i in constellations[-1]:
    constellation.append(i.satellites)
    for j in i.satellites:
        detour_table[j.id] = set()


# while 1:
# while setting == False:
#     # 케플러요소 입력
#     # print("Setting")
#     # inclination = radians(float(Inc(n)))  # 궤도경사
#     # altitude = int(Alt(i))  # 궤도 반지름
#     # orbitNum = OrbNum(o)
#     # satNum = SatNum(s)
#     orbitRot = radians(360 / orbitNum)
#     satRot = radians(360 / satNum)
#     # maxDistance = MaxDist(m)
#     # deploy(inclination, altitude, CONST_COLORS[orbit_cnt])
#     orbit_cnt = (orbit_cnt + 1) % 4
#     setting = not setting

while running == False:
    # print("Running")

    # 타이머 & 핸드오버
    for t in tqdm(range(0, SIMULATION_TIME+1, SLOT_DURATION)):
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

                        # sat.protect_timer[index] += PROTECT_TIME
                        # if sat not in protect_sat_array:
                        #     protect_sat_array.append(sat)
                        # print(sat.handover_timer)
            if 0 not in sat.link_state:
                if sat.id in routing_table:
                    routing_table.remove(sat.id)
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
        if time % 600 == 0:
            rtpg.refresh_rtpg()
        #     for g in ground_stations:
        #         g.reset_connections()
        #         g.connect_satellites(constellations[0])
        if time % 1000 == 0:
            simulator.random_N_to_M_simulation(10)
            # print(len(simulator.network.log))
        # if time % 40000 == 0:
        #     write_routing_simulation_result_partition(simulator.network.log, TOLERABLE_ANGLE_PER_SECOND, time/40000)
        #     simulator.network.reset()
        if time % 80000 == 0:
            print(detour_table)
    running = True
    write_routing_simulation_result(simulator.network.log, TOLERABLE_ANGLE_PER_SECOND)
    # 모든 VPython 객체 제거
    scene.delete()
    vpython.Exit()

    # 프로그램 종료
    sys.exit(0)
    # if running == True:
        #     break

