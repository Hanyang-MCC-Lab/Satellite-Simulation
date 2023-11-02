import math
from time import sleep


def latitude_convert(degree):
    if 90 < degree <= 270:
        return (degree-180) * -1
    elif 270 < degree <= 360:
        return degree - 360
    else:
        return degree
def get_minimum_hop_region(source, destination, max_orbit_num, max_sat_num, constellation):
    src_info, dest_info = source.get_sat_info(), destination.get_sat_info()
    west_distance = ((src_info["orbit"] - dest_info["orbit"]) + max_orbit_num) % max_orbit_num
    east_distance = ((dest_info["orbit"] - src_info["orbit"]) + max_orbit_num) % max_orbit_num
    south_distance = ((src_info["satellite"] - dest_info["satellite"]) + max_sat_num) % max_sat_num
    north_distance = ((dest_info["satellite"] - src_info["satellite"]) + max_sat_num) % max_sat_num
    col_range, row_range = [], []
    src_row, src_col = 0, 0
    dest_row, dest_col = 0, 0
    # 좌 / 우
    if west_distance <= east_distance and west_distance != 0:
        row_range = list(range(dest_info["orbit"], max_orbit_num)) + list(range(src_info["orbit"]))
        src_row, dest_row = len(row_range) - 1, 0
    else:
        row_range = list(range(src_info["orbit"])) + list(range(dest_info["orbit"], max_orbit_num))
        src_row, dest_row = 0, len(row_range) - 1

    # 상 / 하
    if north_distance <= south_distance and north_distance != 0:
        col_range = list(range(src_info["satellite"])) + list(range(dest_info["satellite"], max_sat_num))
        src_col, dest_col = 0, len(col_range) - 1
    else:
        col_range = list(range(dest_info["satellite"], max_sat_num)) + list(range(src_info["satellite"]))
        src_col, dest_col = len(col_range) - 1, 0

    mhr = []
    print(constellation)
    print(row_range, col_range)
    for i in row_range:
        temp = []
        for j in col_range:
            temp.append(constellation[i].satellites[j])
        mhr.append(temp)

    return mhr, src_row, src_col, dest_row, dest_col


def distributed_detour_routing(src, dest, max_orbit_num, max_sat_num, constellation):
    print(src.id, "to", dest.id)
    # direction = 1(상/하 우선), 0(좌/우 우선)
    mhr, src_row, src_col, dest_row, dest_col = get_minimum_hop_region(src, dest, max_orbit_num, max_sat_num,
                                                                       constellation)
    path = []
    dest_info = dest.get_llh_info()
    path.append(src)
    cur_row, cur_col = src_row, src_col
    while path[-1] != dest: # 경로의 마지막이 destination일 때까지
        cur_info = path[-1].get_llh_info()
        sleep(1)
        print("=====", path[-1].id, "=====")
        cur_lat, dest_lat = latitude_convert(cur_info["lat"]), latitude_convert(dest_info["lat"])
        # Primary Direction 결정, Alternative Direction 결정 알고리즘 현재 미개발
        # 추후 추가 예정: 전송 불가(실패) 판단 -> Alternative Direction 결정 & Selective Flooding
        if cur_lat < dest_lat:
            if math.fabs(dest_lat) >= 70:
                if math.fabs(latitude_convert(mhr[cur_row-1][cur_col].get_llh_info()["lat"])) >= 70:
                    direction = 0
                else:
                    direction = 1
            else:
                direction = 1
        elif cur_lat > dest_lat:
            if math.fabs(cur_lat) >= 70:
                direction = 1
            else:
                direction = 0
        else:
            direction = 0

        # Next hop 결정 및 cur 변수 재설정
        if direction > 0:
            if cur_row > dest_row:
                path.append(mhr[cur_row-1][cur_col])
                cur_row -= 1
                print("up")
            else:
                path.append(mhr[cur_row+1][cur_col])
                cur_row += 1
                print("down")
        else:
            if cur_col > dest_col:
                path.append(mhr[cur_row][cur_col-1])
                print("left")
                cur_col -= 1
            else:
                path.append(mhr[cur_row][cur_col+1])
                print("right")
                cur_col += 1

    # 경로 리턴 path <List<Satellite>>
    for i in path:
        print(i.id)
    return path


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
        # if horizontal > 0:  # 위로, 동으로!!
        #     return sat.orbit.orbits[right].satellites[up]
        # elif horizontal < 0:  # 위로, 서로!!
        #     return sat.orbit.orbits[left].satellites[up]
        # else:  # 위로
        return sat.orbit.orbits[cur_info["orbit"]].satellites[up]

    elif vertical < 0:
        # if horizontal > 0:  # 아래로, 동으로!!
        #     return sat.orbit.orbits[right].satellites[down]
        # elif horizontal < 0:  # 아래로, 서로!!
        #     return sat.orbit.orbits[left].satellites[down]
        # else:  # 아래로
        return sat.orbit.orbits[cur_info["orbit"]].satellites[down]
    else:
        if horizontal > 0:  # 동으로
            return sat.orbit.orbits[right].satellites[cur_info["satellite"]]
        else:  # 서로
            return sat.orbit.orbits[left].satellites[cur_info["satellite"]]


def MDD(sat, dest, available_list):
    print(dest)
    smallest_distance = float('inf')
    point_with_smallest_distance = None
    # print("current sat:", self.id)
    # print("available list is")
    for i in available_list:
        if i.id == dest.id:
            return i
        dist = i.get_great_distance(dest)
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


def get_distance_with_lon_and_lat(a_lon, a_lat, b_lon, b_lat):
    lon_node_A = math.radians(a_lon)
    lat_node_A = math.radians(a_lat)
    lon_node_B = math.radians(b_lon)
    lat_node_B = math.radians(b_lat)

    dlon = lon_node_B - lon_node_A
    dlat = lat_node_B - lat_node_A

    a = math.sin(dlat / 2) ** 2 + math.cos(lat_node_A) * math.cos(lat_node_B) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = (6371 + 550) * c
    return distance


def get_nearest_sat(s_lon, s_lat, constellation):
    min_dist = float('inf')
    nearest = None
    for orbits in constellation:
        for orbit in orbits:
            for sat in orbit.satellites:
                llh = sat.get_llh_info()
                temp = get_distance_with_lon_and_lat(s_lon, s_lat, llh["lon"], llh["lat"])
                if min_dist > temp:
                    nearest = sat
                    min_dist = temp

    return nearest
