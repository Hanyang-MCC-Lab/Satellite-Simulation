import numpy as np


def calc_gap_of_angle(a, b):
    # Calculate the magnitudes (norms) of vectors A and B
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Calculate the cosine of the angle between A and B
    cos_angle = np.dot(a, b) / (norm_a * norm_b)
    cos_angle = np.clip(cos_angle, -1, 1)

    # Calculate the angle in radians
    angle_radians = np.arccos(cos_angle)
    return angle_radians


def PAT(sat1, sat2):
    sat2_vec = [sat2.x, sat2.y, sat2.z]
    sat1.local_link_sat_ecef.append(sat2_vec)
    sat1.link_sat.append(sat2)
    sat1.local_link_sat_lla.append([sat2.latitude, sat2.longitude, sat2.altitude])


def re_PAT(sat1, sat2, direction):
    sat2_vec = [sat2.x, sat2.y, sat2.z]
    # print("local(ecef, lla):", sat1.local_link_sat_ecef[direction], sat1.local_link_sat_lla[direction], end=" ")
    sat1.local_link_sat_ecef[direction] = sat2_vec
    sat1.link_sat[direction] = sat2
    sat1.local_link_sat_lla[direction] = [sat2.latitude, sat2.longitude, sat2.altitude]
    # print("local(ecef, lla):", sat1.local_link_sat_ecef[direction], sat1.local_link_sat_lla[direction])


def initialize_lisl(constellation):
    orbit_num = len(constellation)
    sat_num = len(constellation[0].satellites)
    for i in range(orbit_num):
        for j in range(sat_num):
            cur_sat = constellation[i].satellites[j]
            # # intra-orbit
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
