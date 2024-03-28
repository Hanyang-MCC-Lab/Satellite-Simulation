import math

import numpy as np


def calc_angle_between_vectors(a, b):
    # Calculate the magnitudes (norms) of vectors A and B
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Calculate the cosine of the angle between A and B
    cos_angle = np.dot(a, b) / (norm_a * norm_b)
    # cos_angle = np.clip(cos_angle, -1, 1)

    # Calculate the angle in radians
    angle_radians = np.arccos(cos_angle)
    return angle_radians


def PAT(sat1, sat2):
    # o_to_a = np.array([sat1.x, sat1.y, sat1.z])
    # a_to_b = np.array([sat2.x, sat2.y, sat2.z]) - o_to_a
    laser = np.array([sat2.x-sat1.x, sat2.y-sat1.y, sat2.z-sat1.z])
    sat1.laser_vec.append(laser)
    sat1.laser_azimuth.append(math.atan2(laser[1], laser[0]))
    sat1.laser_elevation.append(math.asin(laser[2]/np.linalg.norm(laser)))
    sat1.link_sat.append(sat2)
    # sat1.before_angle_oab_array.append(calc_angle_between_vectors(o_to_a, a_to_b))


def re_PAT(sat1, sat2, direction):
    laser = np.array([sat2.x-sat1.x, sat2.y-sat1.y, sat2.z-sat1.z])
    sat1.laser_vec[direction] = laser
    sat1.laser_azimuth[direction] = math.atan2(laser[1], laser[0])
    sat1.laser_elevation[direction] = math.asin(laser[2]/np.linalg.norm(laser))
    # o_to_a = np.array([sat1.x, sat1.y, sat1.z])
    # a_to_b = np.array([sat2.x, sat2.y, sat2.z]) - o_to_a
    # sat1.before_angle_oab_array[direction] = calc_angle_between_vectors(o_to_a, a_to_b)


def initialize_lisl(constellation):
    orbit_num = len(constellation)
    sat_num = len(constellation[0].satellites)
    for i in range(orbit_num):
        for j in range(sat_num):
            cur_sat = constellation[i].satellites[j]
            # intra-orbit
            # if j == 0:
            #     PAT(cur_sat, constellation[i].satellites[j + 1])
            #     PAT(cur_sat, constellation[i].satellites[sat_num - 1])
            # elif j == sat_num - 1:
            #     PAT(cur_sat, constellation[i].satellites[0])
            #     PAT(cur_sat, constellation[i].satellites[j - 1])
            # else:
            #     PAT(cur_sat, constellation[i].satellites[j + 1])
            #     PAT(cur_sat, constellation[i].satellites[j - 1])
            # inter-orbit
            if i == 0:
                PAT(cur_sat, constellation[orbit_num - 1].satellites[j])
                PAT(cur_sat, constellation[i + 1].satellites[j])
            elif i == orbit_num - 1:
                PAT(cur_sat, constellation[i - 1].satellites[j])
                PAT(cur_sat, constellation[0].satellites[j])
            else:
                PAT(cur_sat, constellation[i - 1].satellites[j])
                PAT(cur_sat, constellation[i + 1].satellites[j])
