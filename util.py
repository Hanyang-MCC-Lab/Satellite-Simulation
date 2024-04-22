import csv
import math
import os

import numpy as np
def set_simulation_result():
    folder_path = f'./SimulationResult/'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = folder_path + 'result.csv'

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
    wr.writerow(title)
    f.close()
def clear_simulation_result():
    filename = f'./SimulationResult/pat_result.csv'
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
        wr.writerow(title)
        file.close()
def write_simulation_result(sat1, sat2, direction, gap, time):
    link_d = ["left", "right"]
    filename = f'./SimulationResult/pat_result.csv'
    f = open(filename, 'a', encoding='utf-8', newline='')
    wr = csv.writer(f)
    s1 = sat1.get_llh_info()
    s2 = sat2.get_llh_info()

    row_data = [sat1.id, s1["lat"], s1["lon"], s1["alt"], sat2.id, s2["lat"], s2["lon"], s2["alt"], link_d[direction], gap, time]
    wr.writerow(row_data)
    f.close()

def write_gap_angle(sat1, sat2, direction, gap, time):
    link_d = ["left", "right"]
    filename = f'./SimulationResult/pat_result.csv'
    f = open(filename, 'a', encoding='utf-8', newline='')
    wr = csv.writer(f)
    s1 = sat1.get_llh_info()
    s2 = sat2.get_llh_info()

    row_data = [sat1.id, s1["lat"], s1["lon"], s1["alt"], sat2.id, s2["lat"], s2["lon"], s2["alt"], link_d[direction], gap, time]
    wr.writerow(row_data)
    f.close()

def write_routing_simulation_result(data):
    filename = f'./SimulationResult/result.csv'
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        wr = csv.writer(file)
        title = []
        title.append('index')
        title.append('source')
        title.append('destination')
        title.append('hops')
        title.append('fail count')
        title.append('delay')
        wr.writerow(title)
        for log in data:
            row_data = [log.index, log.src, log.dst, len(log.path), len(log.fail_info), log.delay]
            wr.writerow(row_data)
        file.close()
def update_ECEF(lat, lon, alt):
    new_x = math.cos(lat) * math.cos(lon) * alt
    new_y = math.cos(lat) * math.sin(lon) * alt
    new_z = math.sin(lat) * alt
    return new_x, new_y, new_z
