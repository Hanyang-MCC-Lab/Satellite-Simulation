import math

import numpy as np


# a: current laser direction vector, satA to SatB
# b: current satA to satB vector
def calc_gap_of_angle(ax, ay, az, bx, by, bz):
    a = np.array([ax, ay, az])  # Replace Ax, Ay, Az with the coordinates of your first vector
    b = np.array([bx, by, bz])  # Replace Bx, By, Bz with the coordinates of your second vector

    # Calculate the magnitudes (norms) of vectors A and B
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    # Calculate the cosine of the angle between A and B
    cos_angle = np.dot(a, b) / (norm_a * norm_b)

    # Calculate the angle in radians
    # angle_radians = np.arccos(cos_angle)
    return cos_angle


# def rotate_position(delta_lat, delta_lon, x, y, z):
#
#     # Longitude rotation (around the Z-axis)
#     R_lon = np.array([
#         [np.cos(delta_lon), -np.sin(delta_lon), 0],
#         [np.sin(delta_lon), np.cos(delta_lon), 0],
#         [0, 0, 1]
#     ])
#
#     # Latitude rotation (around the X-axis)
#     # Note the direction of the latitude change is negative here
#     # R_lat = np.array([
#     #     [1, 0, 0],
#     #     [0, np.cos(-delta_lat), -np.sin(-delta_lat)],
#     #     [0, np.sin(-delta_lat), np.cos(-delta_lat)]
#     # ])
#
#     position = np.array([x, y, z])
#     update_pos = R_lon.dot(position)
#
#     return update_pos[0], update_pos[1], update_pos[2]

def update_ECEF(lat, lon, alt):
    new_x = math.cos(lat) * math.cos(lon) * alt
    new_y = math.cos(lat) * math.sin(lon) * alt
    new_z = math.sin(lat) * alt
    return new_x, new_y, new_z
