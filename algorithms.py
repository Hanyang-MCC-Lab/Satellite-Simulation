import math
import random
from time import sleep

from vpython import vec, color


def latitude_convert(degree):
    if 90 < degree <= 270:
        return (degree - 180) * -1
    elif 270 < degree <= 360:
        return degree - 360
    else:
        return degree


def get_minimum_hop_region(source, destination, max_orbit_num, max_sat_num, constellation):
    src_info, dest_info = source.get_sat_info(), destination.get_sat_info()
    south_distance = ((src_info["satellite"] - dest_info["satellite"]) + max_sat_num) % max_sat_num
    north_distance = ((dest_info["satellite"] - src_info["satellite"]) + max_sat_num) % max_sat_num
    west_distance = ((src_info["orbit"] - dest_info["orbit"]) + max_orbit_num) % max_orbit_num
    east_distance = ((dest_info["orbit"] - src_info["orbit"]) + max_orbit_num) % max_orbit_num
    orbit_range, sat_range = [], []
    src_sat, src_orbit = 0, 0
    dest_sat, dest_orbit = 0, 0
    # 좌 / 우
    if west_distance <= east_distance:  # 오른쪽으로 이동
        if src_info["orbit"] < dest_info["orbit"]:  # 오른쪽으로 가는데 중간에 0이 있음
            orbit_range = list(range(dest_info["orbit"], max_orbit_num)) + list(
                range(src_info["orbit"] + 1))
        else:  # 오른쪽으로 가는데 중간에 0이 없음
            orbit_range = list(range(dest_info["orbit"], src_info["orbit"] + 1))
        src_orbit, dest_orbit = len(orbit_range) - 1, 0
    else:  # 왼쪽으로 이동
        if src_info["orbit"] > dest_info["orbit"]:  # 왼쪽으로 가는데 중간에 0이 있음
            orbit_range = list(range(src_info["orbit"], max_orbit_num)) + list(
                range(dest_info["orbit"] + 1))
        else:  # 왼쪽으로 가는데 중간에 0이 없음
            orbit_range = list(range(src_info["orbit"], dest_info["orbit"] + 1))
        src_orbit, dest_orbit = 0, len(orbit_range) - 1

    # 상 / 하
    if north_distance <= south_distance:  # 북으로 감
        if src_info["satellite"] > dest_info["satellite"]:  # 북으로 가는데 중간에 0이 있음
            sat_range = list(range(dest_info["satellite"], -1, -1)) + list(
                range(max_sat_num - 1, src_info["satellite"] - 1, -1))
        else:  # 북으로 가는데 중간에 0이 없음
            sat_range = list(range(dest_info["satellite"], src_info["satellite"] - 1, -1))
        src_sat, dest_sat = len(sat_range) - 1, 0
    else:  # 남으로 감
        if src_info["satellite"] < dest_info["satellite"]:  # 남으로 가는데 중간에 0이 있음
            sat_range = list(range(src_info["satellite"], -1, -1)) + list(
                range(max_sat_num - 1, dest_info["satellite"] - 1, -1))
        else:  # 남으로 가는데 중간에 0이 없음
            sat_range = list(range(src_info["satellite"], dest_info["satellite"] - 1, -1))
        src_sat, dest_sat = 0, len(sat_range) - 1

    mhr = []
    # print(orbit_range)
    # print(sat_range)
    # print("src: ", src_orbit, src_sat)
    # print("dst: ", dest_orbit, dest_sat)
    for i in sat_range:
        temp = []
        for j in orbit_range:
            temp.append(constellation[j].satellites[i])
        mhr.append(temp)

    return mhr, src_sat, src_orbit, dest_sat, dest_orbit


def extend_mhr(constellation, mhr, direction):
    mhr_extended = []
    extend_sat_index = 0
    satnum = len(constellation)
    if direction == "up":
        extend_sat_index = (mhr[0][0].get_sat_info()["satellite"] + 1) % satnum
    if direction == "down":
        extend_sat_index = (mhr[-1][0].get_sat_info()["satellite"] - 1) if mhr[0][0].get_sat_info()[
                                                                               "satellite"] > 0 else 0
    for i in mhr[0]:
        mhr_extended.append(constellation[i.get_sat_info()["orbit"]].satellites[extend_sat_index])
    result = []
    if direction == "up":
        result.append(mhr_extended)
        for i in mhr:
            result.append(i)
        return result
    else:
        mhr.append(mhr_extended)
        return mhr


def get_optimal_row_line(mhr, src_sat, dest_sat):
    best_latitude_line = src_sat
    best_latitude = math.fabs(latitude_convert(mhr[best_latitude_line][0].get_llh_info()["lat"]))
    if src_sat == dest_sat: return src_sat
    if src_sat == 0:
        for_range = range(1, len(mhr))
    else:
        for_range = range(src_sat - 1, -1, -1)
    for idx in for_range:
        temp = math.fabs(latitude_convert(mhr[idx][0].get_llh_info()["lat"]))
        if best_latitude < temp:
            best_latitude_line = idx
            best_latitude = temp
    return best_latitude_line


def distributed_detour_routing(constellation, mhr, src_sat, src_orbit, dest_sat, dest_orbit, src, dest):
    # print(src.id, "to", dest.id)
    opt_line = get_optimal_row_line(mhr, src_sat, dest_sat)
    need_flood = False
    path = []
    fail_info = []
    fail_history = []
    count = 0
    print("===MHR===")
    for i in mhr:
        for j in i:
            print(j.id, end=" ")
        print()
    # print("length", len(mhr))
    dest_info = dest.get_llh_info()
    cur_sat, cur_orbit = src_sat, src_orbit
    while cur_sat != dest_sat or cur_orbit != dest_orbit:  # 경로의 마지막이 destination일 때까지
        sleep(0.1)
        success = True
        path.append(mhr[cur_sat][cur_orbit])
        cur_info = mhr[cur_sat][cur_orbit].get_llh_info()
        cur_id = mhr[cur_sat][cur_orbit].id
        print("=====", mhr[cur_sat][cur_orbit].id, "=====")
        print("cur_sat", cur_sat, "cur_orbit", cur_orbit)
        print("current:", cur_sat, cur_orbit)
        if dest.id in mhr[cur_sat][cur_orbit].detourTable:
            # detour table에 의한 라우팅
            print(cur_id, "has a direction in its detour table!")
            direction = mhr[cur_sat][cur_orbit].detourTable[dest.id]
            # 링크 상태를 고려함
            if direction == "right":
                success = True if mhr[cur_sat][cur_orbit].link_state[1] == 1 else False
            elif direction == "left":
                success = True if mhr[cur_sat][cur_orbit].link_state[0] == 1 else False

        else:
            # 일반 라우팅
            # step1. 방향결정
            direction = get_direction(cur_orbit, dest_orbit, src_orbit, cur_sat, dest_sat, src_orbit, opt_line)
            # if (cur_orbit != dest_orbit and cur_sat == vertical_line) or need_flood:
            #     if cur_orbit > dest_orbit:
            #         direction = "left"
            #     else:
            #         direction = "right"
            # else:
            #     if cur_sat > dest_sat:
            #         direction = "up"
            #     else:
            #         direction = "down"

            if (direction == "left" and mhr[cur_sat][cur_orbit].link_state[0] == 0) or (direction == "right" and mhr[cur_sat][cur_orbit].link_state[1] == 0):
                success = False
            else:
                success = True

            if need_flood:
                fail_info[-1][-1].fail_experiences[0 if direction == "left" else 1].append(
                    selective_flood(mhr, src_sat, src_orbit, cur_sat, cur_orbit, dest, direction
                                    ))
                need_flood = False

        # step2. 성공/실패에 따른 알고리즘 분리
        if success:  # 성공
            if direction == "up":
                cur_sat -= 1
            elif direction == "down":
                cur_sat += 1
            elif direction == "left":
                cur_orbit -= 1
            else:  # direction == "right"
                cur_orbit += 1
            # print("next hop is", mhr[cur_sat][cur_orbit].id)
        else:  # 실패
            # print("!!!!! Fail to transmit on", mhr[cur_sat][cur_orbit].id, "!!!!!")
            need_flood = True
            sec_direction = ""
            fail_history.append((cur_sat, cur_orbit))
            fail_sat, fail_orbit = cur_sat, cur_orbit
            fail_pair = [mhr[cur_sat][cur_orbit]]
            # if direction == "up":
            #     fail_pair.append(mhr[cur_sat-1][cur_orbit])
            # elif direction == "down":
            #     fail_pair.append(mhr[cur_sat+1][cur_orbit])
            if direction == "left":
                fail_pair.append(mhr[cur_sat][cur_orbit - 1])
            else:
                fail_pair.append(mhr[cur_sat][cur_orbit + 1])
            fail_info.append(fail_pair)
            mhr[cur_sat][cur_orbit].should_notice_recovery = True
            # selective_flood(mhr, src_sat, src_orbit, dest_sat, dest_orbit, cur_sat, cur_orbit, dest, direction)
            if src_sat > dest_sat:
                sec_direction = "up"
            else:
                sec_direction = "down"
            cur_sat += 1 if sec_direction == "down" else -1
            if cur_sat >= len(mhr) or cur_sat < 0:
                mhr = extend_mhr(constellation, mhr, sec_direction)
                if sec_direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
                    cur_sat += 1
                    src_sat += 1
                    dest_sat += 1
                print("extending mhr")
                print("===MHR===")
                print(mhr)
                for i in mhr:
                    for j in i:
                        print(j.id, end=" ")
                    print()
            print("move instantly to", mhr[cur_sat][cur_orbit].id)
        count += 1
    path.append(mhr[cur_sat][cur_orbit])

    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_info
    # return path


def selective_flood(mhr, src_sat, src_orbit, fail_sat, fail_orbit, destination, sec_direction):
    # 진행 경우, 1. inter-intra, 2. intra-inter, 3. intra-inter-intra
    # print(sec_direction)
    flood_path = []
    flood_direction = {"down": (-1, 0), "up": (1, 0), "right": (0, -1), "left": (0, 1)}
    csat, corb = fail_sat, fail_orbit
    dsat, dorb = flood_direction[sec_direction]
    # if fail_sat == dest_sat and fail_sat != src_sat and fail_orbit == src_orbit: # intra먼저 했고, inter첫번째에서 터짐
    #     if fail_sat == 0:
    #         print(1)
    #         if fail_orbit < dest_orbit:
    #             mhr[fail_sat+1][fail_orbit].detourTable[destination.id] = "right"
    #         if fail_orbit > dest_orbit:
    #             mhr[fail_sat+1][fail_orbit].detourTable[destination.id] = "left"
    #         flood_path.append(mhr[fail_sat+1][fail_orbit])
    #     else:
    #         print(2)
    #         if fail_orbit < dest_orbit:
    #             mhr[fail_sat-1][fail_orbit].detourTable[destination.id] = "right"
    #         if fail_orbit > dest_orbit:
    #             mhr[fail_sat-1][fail_orbit].detourTable[destination.id] = "left"
    #         flood_path.append(mhr[fail_sat-1][fail_orbit])

    mhr[csat][corb].detourTable[destination.id] = sec_direction
    flood_path.append(mhr[csat][corb])
    while csat != src_sat and corb != src_orbit:
        csat, corb = csat + dsat, corb + dorb
        try:
            mhr[csat][corb].detourTable[destination.id] = sec_direction
        except IndexError:
            print(f'index error: {csat}, {corb}')
        flood_path.append(mhr[csat][corb])

    # print("flood path: ", end="")
    # for fsat in flood_path:
    #     print(fsat.id, end=" ")
    # print()

    return [flood_path, destination.id]



def new_selective_flood(mhr, src_sat, src_orbit, fail_sat, fail_orbit, dest_sat, dest_orbit, destination,
                        failed_direction):
    flood_path = []
    if fail_sat == dest_sat and fail_orbit == src_orbit:  # intra먼저 했고, inter첫번째에서 터짐
        if fail_sat == 0:
            if fail_orbit < dest_orbit:
                mhr[fail_sat + 1][fail_orbit].detourTable[destination.id] = "right"
            if fail_orbit > dest_orbit:
                mhr[fail_sat + 1][fail_orbit].detourTable[destination.id] = "left"
            flood_path.append(mhr[fail_sat + 1][fail_orbit])
        else:
            if fail_orbit < dest_orbit:
                mhr[fail_sat - 1][fail_orbit].detourTable[destination.id] = "right"
            if fail_orbit > dest_orbit:
                mhr[fail_sat - 1][fail_orbit].detourTable[destination.id] = "left"
            flood_path.append(mhr[fail_sat - 1][fail_orbit])

    elif fail_sat == src_sat and fail_orbit != src_orbit:  # inter먼저 하는데 덜 됨
        # print("is in src sat line")
        if src_sat == 0:
            mhr[fail_sat][fail_orbit].detourTable[destination.id] = "down"
        else:
            mhr[fail_sat][fail_orbit].detourTable[destination.id] = "up"
        flood_path.append(mhr[fail_sat][fail_orbit])

    elif fail_sat != src_sat and fail_orbit != dest_orbit:  # intra하고 inter중 터짐
        if failed_direction == "left":
            if fail_sat < src_sat:
                for orbit in range(fail_orbit, src_orbit + 1):
                    mhr[fail_sat + 1][orbit].detourTable[destination.id] = "left"
                    flood_path.append(mhr[fail_sat + 1][orbit])
            if fail_sat > src_sat:
                for orbit in range(fail_orbit, src_orbit + 1):
                    mhr[fail_sat - 1][orbit].detourTable[destination.id] = "left"
                    flood_path.append(mhr[fail_sat - 1][orbit])
        elif failed_direction == "right":
            if fail_sat < src_sat:
                for orbit in range(src_orbit, fail_orbit + 1):
                    mhr[fail_sat + 1][orbit].detourTable[destination.id] = "right"
                    flood_path.append(mhr[fail_sat + 1][orbit])
            if fail_sat > src_sat:
                for orbit in range(src_orbit, fail_orbit + 1):
                    mhr[fail_sat - 1][orbit].detourTable[destination.id] = "right"
                    flood_path.append(mhr[fail_sat - 1][orbit])
    return [flood_path, destination]


def recovery_flood(sat, index):
    for flood_path in sat.fail_experiences[index]:
        dest = flood_path[1]
        for i in flood_path[0]:
            # print(dest, i.detourTable)
            if dest in i.detourTable:
                del i.detourTable[dest]


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


def get_direction(cur_orbit, dest_orbit, src_orbit, cur_sat, dest_sat, src_sat, opt_line):
    if cur_orbit != dest_orbit and \
            (((cur_sat == opt_line) or (dest_sat <= cur_sat < opt_line) or (opt_line < cur_sat <= dest_sat)) or
             ((src_sat <= dest_sat < cur_sat) or (cur_sat < dest_sat <= src_sat))):
        if cur_orbit > dest_orbit:
            direction = "left"
        else:
            direction = "right"
    else:
        if cur_sat > dest_sat:
            direction = "up"
        else:
            direction = "down"
    return direction


def n_hop_flood(n, mhr, dest_sat, dest_orbit, src_orbit, cur_sat, cur_orbit, src_sat, opt_line, dest, direction):
    visited = []
    flood_path = []
    direction_to_ds_do = {"down": (-1, 0), "up": (1, 0), "right": (0, -1), "left": (0, 1)}
    flood_direction = [(1, 0, "up"), (-1, 0, "down"), (0, 1, "left"), (0, -1, "right")]
    vertical_len, horizontal_len = len(mhr), len(mhr[0])
    queue = [(cur_sat, cur_orbit, direction)]
    while n >= 0:
        round_arr = []
        while len(queue) > 0:
            cur_s, cur_o, from_direction = queue.pop()
            round_arr.append((cur_s, cur_o))
            if (cur_s, cur_o) in visited:
                pass
            else:
                flood_path.append(mhr[cur_s][cur_o])
                visited.append((cur_s, cur_o))
                detour_direction = get_direction(cur_o, dest_orbit, src_orbit, cur_s, dest_sat, src_sat, opt_line)
                if detour_direction == from_direction:
                    if detour_direction in ["right", "left"]:
                        pass
                        if src_sat <= dest_sat:
                            detour_direction = "down"
                        else:
                            detour_direction = "up"
                    else:
                        if cur_o < dest_orbit:
                            detour_direction = "right"
                        else:
                            detour_direction = "left"
                    if detour_direction == ["up", "down"]:
                        if src_sat <= dest_sat:
                            detour_direction = "down"
                        else:
                            detour_direction = "up"
                        pass
                        # ds, do = direction_to_ds_do[detour_direction]
                        # if 0 <= cur_s < vertical_len:
                        #     if dest.id in mhr[cur_s + ds][cur_o + do].detourTable:
                        #         if detour_direction == "up" and mhr[cur_s + ds][cur_o + do].detourTable[dest.id] == "down":
                        #             detour_direction = "down"
                        #         elif detour_direction == "down" and mhr[cur_s + ds][cur_o + do].detourTable[dest.id] == "up":
                        #             detour_direction = "up"
                # print(mhr[cur_s][cur_o].id, "detour direction:", detour_direction)
                mhr[cur_s][cur_o].detourTable[dest.id] = detour_direction
        for cur_s, cur_o in round_arr:
            if n > 0:
                for ds, do, new_f_d in flood_direction:
                    if 0 <= cur_s + ds < vertical_len and 0 <= cur_o + do < horizontal_len:
                        # if new_f_d in ["left", "right"] and mhr[cur_s][cur_o].link_state[0 if new_f_d == "left" else 1] == 1:
                        queue.append((cur_s + ds, cur_o + do, new_f_d))
        n -= 1

    return [flood_path, dest.id]


def dtdr(constellation, mhr, src_sat, src_orbit, dest_sat, dest_orbit, src, dest):
    # print(src.id, "to", dest.id)
    opt_line = get_optimal_row_line(mhr, src_sat, dest_sat)
    path = []
    fail_info = []
    fail_history = []
    count = 0
    # print("===MHR===")
    # for i in mhr:
    #     for j in i:
    #         print(j.id, end=" ")
    #     print()
    # print("length", len(mhr))
    dest_info = dest.get_llh_info()
    cur_sat, cur_orbit = src_sat, src_orbit
    while cur_sat != dest_sat or cur_orbit != dest_orbit:  # 경로의 마지막이 destination일 때까지
        # sleep(0.1)
        success = True
        path.append(mhr[cur_sat][cur_orbit])
        cur_info = mhr[cur_sat][cur_orbit].get_llh_info()
        cur_id = mhr[cur_sat][cur_orbit].id
        # print("=====", mhr[cur_sat][cur_orbit].id, "=====")
        # print("cur_sat", cur_sat, "cur_orbit", cur_orbit)
        if dest.id in mhr[cur_sat][cur_orbit].detourTable:
            # detour table에 의한 라우팅
            # print(cur_id, "has a direction in its detour table!")
            direction = mhr[cur_sat][cur_orbit].detourTable[dest.id]
            # 링크 상태를 고려함
            if direction == "right":
                success = True if mhr[cur_sat][cur_orbit].link_state[1] == 1 else False
            elif direction == "left":
                success = True if mhr[cur_sat][cur_orbit].link_state[0] == 1 else False

        else:
            # 일반 라우팅
            # step1. 방향결정
            direction = get_direction(cur_orbit, dest_orbit, src_orbit, cur_sat, dest_sat, src_sat, opt_line)

        if (direction == "left" and mhr[cur_sat][cur_orbit].link_state[0] == 0) or (
                direction == "right" and mhr[cur_sat][cur_orbit].link_state[1] == 0):
            success = False
        else:
            success = True

        # step2. 성공/실패에 따른 알고리즘 분리
        if success:  # 성공
            if direction == "up":
                cur_sat -= 1
            elif direction == "down":
                cur_sat += 1
            elif direction == "left":
                cur_orbit -= 1
            else:  # direction == "right"
                cur_orbit += 1
            # print("next hop is", mhr[cur_sat][cur_orbit].id)
        else:  # 실패
            # print("!!!!! Fail to transmit on", mhr[cur_sat][cur_orbit].id, "!!!!!")
            sec_direction = ""
            fail_history.append((cur_sat, cur_orbit))
            fail_sat, fail_orbit = cur_sat, cur_orbit
            fail_pair = [mhr[cur_sat][cur_orbit]]
            if direction == "left":
                fail_pair.append(mhr[cur_sat][cur_orbit - 1])
            else:
                fail_pair.append(mhr[cur_sat][cur_orbit + 1])
            fail_info.append(fail_pair)
            fail_info[-1][-1].should_notice_recovery = True
            fail_info[-1][-1].fail_experiences[0 if direction == "left" else 1].append(
                n_hop_flood(2, mhr, dest_sat, dest_orbit, src_orbit, cur_sat, cur_orbit, src_sat, opt_line, dest, direction)
            )
            sec_direction = mhr[cur_sat][cur_orbit].detourTable[dest.id]
            cur_sat += 1 if sec_direction == "down" else -1
            if cur_sat >= len(mhr) or cur_sat < 0:
                mhr = extend_mhr(constellation, mhr, sec_direction)
                if sec_direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
                    cur_sat += 1
                    src_sat += 1
                    dest_sat += 1
            #     print("extending mhr")
            #     print("===MHR===")
            #     print(mhr)
            #     for i in mhr:
            #         for j in i:
            #             print(j.id, end=" ")
            #         print()
            # print("move instantly to", mhr[cur_sat][cur_orbit].id)
        count += 1
    path.append(mhr[cur_sat][cur_orbit])

    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_info
