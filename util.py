import csv
import math
import os

import numpy as np

from parameter import ALGORITHM


def set_simulation_result(gamma):
    folder_path = f'./SimulationResult/{ALGORITHM}/'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = folder_path + f'{ALGORITHM}pat_result{gamma}.csv'

    f = open(filename, 'w', encoding='utf-8', newline='')
    wr = csv.writer(f)
    title = []
    title.append('S1_id')
    title.append('S1_lat')
    title.append('S1_lon')
    title.append('S1_alt')
    title.append('S2_id')
    title.append('S2_lat')
    title.append('S2_lon')
    title.append('S2_alt')
    title.append('link direction')
    title.append('gap of angle (rad)')
    title.append('time')
    title.append('distance')
    wr.writerow(title)
    f.close()
def clear_simulation_result(gamma):
    filename = f'./SimulationResult/{ALGORITHM}/{ALGORITHM}pat_result{gamma}.csv'
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        wr = csv.writer(file)
        title = []
        title.append('S1_id')
        title.append('S1_lat')
        title.append('S1_lon')
        title.append('S1_alt')
        title.append('S2_id')
        title.append('S2_lat')
        title.append('S2_lon')
        title.append('S2_alt')
        title.append('link direction')
        title.append('gap of angle (rad)')
        title.append('time')
        title.append('distance')
        wr.writerow(title)
        file.close()
def write_simulation_result(sat1, sat2, direction, gap, time, gamma, distance):
    link_d = ["left", "right"]
    filename = f'./SimulationResult/{ALGORITHM}/{ALGORITHM}pat_result{gamma}.csv'
    f = open(filename, 'a', encoding='utf-8', newline='')
    wr = csv.writer(f)
    s1 = sat1.get_llh_info()
    s2 = sat2.get_llh_info()

    row_data = [sat1.id, math.degrees(sat1.true_anomaly), s1["lon"], s1["alt"], sat2.id, s2["lat"], s2["lon"], s2["alt"], link_d[direction], gap, time, distance]
    wr.writerow(row_data)
    f.close()

def set_routing_simulation_result(gamma):
    filename = f'./SimulationResult/{ALGORITHM}/{ALGORITHM}result{gamma}.csv'
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        wr = csv.writer(file)
        title = ['index', 'source', 'destination', 'hops', 'fail count', 'delay', 'overhead_signal']
        wr.writerow(title)
        file.close()
def write_routing_simulation_result(data, gamma):
    print(data)
    filename = f'./SimulationResult/{ALGORITHM}/{ALGORITHM}result{gamma}.csv'
    with open(filename, 'a', encoding='utf-8', newline='') as file:
        wr = csv.writer(file)
        for log in data:
            row_data = [log.index, log.src.id, log.dst.id, len(log.path), len(log.fail_info), log.delay, log.overhead_signal]
            wr.writerow(row_data)
        file.close()
def update_ECEF(inc, true_anomaly, ascending_node, alt):
    sin_ascend, cos_ascend = math.sin(ascending_node), math.cos(ascending_node)
    sin_true, cos_true = math.sin(true_anomaly), math.cos(true_anomaly)
    sin_inc, cos_inc = math.sin(inc), math.cos(inc)
    x = alt * (cos_ascend*cos_true - sin_ascend*sin_true*cos_inc)
    y = alt * (sin_ascend*cos_true + cos_ascend*sin_true*cos_inc)
    z = alt * sin_true * sin_inc
    # vx = -1*cos_ascend*cos_true - sin_ascend*sin_true*cos_inc
    # vy = -1*sin_ascend*cos_true + cos_ascend*sin_true*cos_inc
    # vz = sin_true * sin_inc
    return x, y, z
    # new_x = math.cos(lat) * math.cos(lon) * alt
    # new_y = math.cos(lat) * math.sin(lon) * alt
    # new_z = math.sin(lat) * alt
    # return new_x, new_y, new_z
