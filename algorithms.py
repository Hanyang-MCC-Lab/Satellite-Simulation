import math


def TEW(sat, cur_info, dest_info, orbitNum, satNum):
    # 이전 알고리즘 : 8방향
    horizontal, vertical = 0, 0
    # 왼쪽 & 오른쪽 방향선택
    west_distance = ((cur_info["orbit"] - dest_info["orbit"]) + orbitNum) % orbitNum
    east_distance = ((dest_info["orbit"] - cur_info["orbit"]) + orbitNum) % orbitNum
    if west_distance <= east_distance and west_distance != 0:
        horizontal = -1
    elif west_distance > east_distance:
        horizontal = 1
    # 위 & 아래 방향선택
    south_distance = ((cur_info["satellite"] - dest_info["satellite"]) + satNum) % satNum
    north_distance = ((dest_info["satellite"] - cur_info["satellite"]) + satNum) % satNum
    if north_distance <= south_distance and north_distance != 0:
        vertical = 1
    elif north_distance > south_distance:
        vertical = -1
    # 적합한 위성 리턴
    right, left = ((cur_info["orbit"] + 1) + orbitNum) % orbitNum, ((cur_info["orbit"] - 1) + orbitNum) % orbitNum
    up, down = ((cur_info["satellite"] + 1) + satNum) % satNum, ((cur_info["satellite"] - 1) + satNum) % satNum
    if vertical > 0:
        if horizontal > 0:  # 위로, 동으로
            return sat.orbit.orbits[right].satellites[up]
        elif horizontal < 0:  # 위로, 서로
            return sat.orbit.orbits[left].satellites[up]
        else:  # 위로
            return sat.orbit.orbits[cur_info["orbit"]].satellites[up]

    elif vertical < 0:
        if horizontal > 0:  # 아래로, 동으로
            return sat.orbit.orbits[right].satellites[down]
        elif horizontal < 0:  # 아래로, 서로
            return sat.orbit.orbits[left].satellites[down]
        else:  # 아래로
            return sat.orbit.orbits[cur_info["orbit"]].satellites[down]
    else:
        if horizontal > 0:  # 동으로
            return sat.orbit.orbits[right].satellites[cur_info["satellite"]]
        else:  # 서로
            return sat.orbit.orbits[left].satellites[cur_info["satellite"]]


def MDD(sat, dest, available_list):
    smallest_distance = float('inf')
    point_with_smallest_distance = None
    # print("current sat:", self.id)
    # print("available list is")
    for i in available_list:
        if i.id == dest.id:
            return i
        dist = sat.get_great_distance(i, dest)
        # print(available_list[i].id, "  distance:", dist)
        if dist < smallest_distance:
            smallest_distance = dist
            point_with_smallest_distance = i
    # print("====================================")

    return point_with_smallest_distance


def calculate_vector(point1, point2):
    if len(point1) != 3 or len(point2) != 3:
        raise ValueError("Both points must be 3D coordinates.")

    vector = [point2[0] - point1[0], point2[1] - point1[1], point2[2] - point1[2]]
    return vector


def calculate_angle(vector1, vector2):
    dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
    magnitude1 = math.sqrt(sum(v1 ** 2 for v1 in vector1))
    magnitude2 = math.sqrt(sum(v2 ** 2 for v2 in vector2))
    cosine_similarity = dot_product / (magnitude1 * magnitude2)

    # Ensure the value is within the valid range for acos ([-1, 1])
    cosine_similarity = min(max(cosine_similarity, -1), 1)

    angle_in_radians = math.acos(cosine_similarity)
    angle_in_degrees = math.degrees(angle_in_radians)
    return angle_in_degrees


def MDA(sat, dest, available_list):
    src_ecef = sat.get_ecef_info()
    dest_ecef = dest.get_ecef_info()
    smallest_angle = float('inf')
    point_with_smallest_angle = None

    vector = calculate_vector(src_ecef, dest_ecef)

    for i in available_list:
        vector2 = calculate_vector(src_ecef, i.get_ecef_info())
        angle = calculate_angle(vector, vector2)

        if angle < smallest_angle:
            smallest_angle = angle
            point_with_smallest_angle = i

    return point_with_smallest_angle
