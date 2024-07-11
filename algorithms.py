import math
import random
from time import sleep
from RTPG import minimum_hop_estimate
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


def new_mhr(source, destination, constellation):
    horizontal, vertical = minimum_hop_estimate(source, destination)
    src_sat, src_orbit, dest_sat, dest_orbit = 0, 0, 0, 0
    mhr = []
    # print(horizontal, vertical)
    if horizontal >= 0:
        if vertical >= 0:  # 우상향
            cur = source
            # print(cur.link)
            for i in range(vertical + 1):
                row = []
                point = cur
                for j in range(horizontal + 1):
                    row.append(cur)
                    cur = cur.link["right"]
                mhr.insert(0, row)
                cur = point.link["up"]
            src_sat, src_orbit = vertical, 0
            dest_sat, dest_orbit = 0, horizontal

        elif vertical < 0:  # 우하향
            cur = source
            for i in range(abs(vertical) + 1):
                row = []
                point = cur
                for j in range(horizontal + 1):
                    row.append(cur)
                    cur = cur.link["right"]
                mhr.append(row)
                cur = point.link["down"]
            src_sat, src_orbit = 0, 0
            dest_sat, dest_orbit = abs(vertical), horizontal
    else:
        if vertical >= 0:  # 좌상향
            cur = source
            for i in range(vertical + 1):
                row = []
                point = cur
                for j in range(abs(horizontal) + 1):
                    row.insert(0, cur)
                    cur = cur.link["left"]
                mhr.insert(0, row)
                cur = point.link["up"]
            src_sat, src_orbit = vertical, abs(horizontal)
            dest_sat, dest_orbit = 0, 0

        elif vertical < 0:  # 좌하향
            cur = source
            for i in range(abs(vertical) + 1):
                row = []
                point = cur
                for j in range(abs(horizontal) + 1):
                    row.insert(0, cur)
                    cur = cur.link["left"]
                mhr.append(row)
                cur = point.link["down"]
            src_sat, src_orbit = 0, abs(horizontal)
            dest_sat, dest_orbit = abs(vertical), 0

    # print(orbit_range)
    # print(sat_range)
    # print("===MHR===")
    # for i in mhr:
    #     for j in i:
    #         print(j.id, end=" ")
    #     print()
    # print("src: ", src_orbit, src_sat)
    # print("dst: ", dest_orbit, dest_sat)

    return mhr, src_sat, src_orbit, dest_sat, dest_orbit


def extend_mhr(mhr, direction):
    mhr_extended = []
    horizontal = len(mhr[0])

    if direction == "up":
        sat = 0
    else:
        sat = -1

    for i in range(horizontal):
        mhr_extended.append(mhr[sat][i].link[direction])

    if direction == "up":
        mhr.insert(0, mhr_extended)
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
    overhead_signal = 0
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
        first_direction, second_direction = new_get_direction(cur_orbit, dest_orbit, cur_sat, dest_sat, src_sat,
                                                              opt_line)
        # print("=====", mhr[cur_sat][cur_orbit].id, "=====")
        # print("cur_sat", cur_sat, "cur_orbit", cur_orbit)
        # print("current:", cur_sat, cur_orbit)
        if second_direction is None:
            direction = first_direction
        else:
            if dest.id in mhr[cur_sat][cur_orbit].detourTable:
                # detour table에 의한 라우팅
                # ####### debugging print ########
                # print(cur_id, "has a direction in its detour table!")
                direction = second_direction
            else:
                # 일반 라우팅
                direction = first_direction
                if (prev_dir == "up" and direction == "down") or (prev_dir == "down" and direction == "up"):
                    direction = second_direction

            if (direction == "left" and mhr[cur_sat][cur_orbit].link_state[0] == 0) or (
                    direction == "right" and mhr[cur_sat][cur_orbit].link_state[1] == 0):
                success = False
            else:
                success = True

            if need_flood:
                flood_return = selective_flood(mhr, src_sat, src_orbit, cur_sat, cur_orbit, dest, direction)
                overhead_signal += len(flood_return[0])
                fail_info[-1][0].fail_experiences[0 if direction == "left" else 1].append(flood_return)
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

            prev_dir = direction
        else:  # 실패
            # print("!!!!! Fail to transmit on", mhr[cur_sat][cur_orbit].id, "!!!!!")
            need_flood = True
            fail_history.append((cur_sat, cur_orbit))
            fail_pair = [mhr[cur_sat][cur_orbit]]

            if direction == "left":
                fail_pair.append(mhr[cur_sat][cur_orbit - 1])
            else:
                fail_pair.append(mhr[cur_sat][cur_orbit + 1])
            fail_info.append(fail_pair)
            fail_pair[-1].should_notice_recovery = True

            direction = second_direction
            cur_sat += 1 if direction == "down" else -1

            if cur_sat >= len(mhr) or cur_sat < 0:
                mhr = extend_mhr(mhr, direction)
                if direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
                    cur_sat += 1
                    src_sat += 1
                    dest_sat += 1
                # opt_line = cur_sat
                # print("extending mhr")
                # print("===MHR===")
                # print(mhr)
                # for i in mhr:
                #     for j in i:
                #         print(j.id, end=" ")
                #     print()
            # print("move instantly to", mhr[cur_sat][cur_orbit].id)
    path.append(mhr[cur_sat][cur_orbit])

    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_info, overhead_signal
    # return path


def selective_flood(mhr, src_sat, src_orbit, fail_sat, fail_orbit, destination, sec_direction):
    # 진행 경우, 1. inter-intra, 2. intra-inter, 3. intra-inter-intra
    # print(sec_direction)
    flood_path = []
    flood_direction = {"down": (-1, 0), "up": (1, 0), "right": (0, -1), "left": (0, 1)}
    csat, corb = fail_sat, fail_orbit
    dsat, dorb = flood_direction[sec_direction]

    mhr[csat][corb].detourTable[destination.id] = sec_direction
    flood_path.append(mhr[csat][corb])
    while csat != src_sat and corb != src_orbit:
        csat, corb = csat + dsat, corb + dorb
        try:
            mhr[csat][corb].detourTable[destination.id] = sec_direction
        except IndexError:
            print(f'detour point: {fail_sat}, {fail_orbit} sec_direction: {sec_direction}')
            print(f'index error: {csat}, {corb}')
            print("===MHR===")
            print(mhr)
            for i in mhr:
                for j in i:
                    print(j.id, end=" ")
                print()
        flood_path.append(mhr[csat][corb])

    # print("flood path: ", end="")
    # for fsat in flood_path:
    #     print(fsat.id, end=" ")
    # print()

    return [flood_path, destination.id]


def recovery_flood(sat, index):
    for flood_path in sat.fail_experiences[index]:
        dest = flood_path[1]
        for i in flood_path[0]:
            # print(dest, i.detourTable)
            if dest in i.detourTable:
                i.detourTable.remove(dest)


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


def new_get_direction(cur_orbit, dest_orbit, cur_sat, dest_sat, src_sat, opt_line):
    first, second = None, None
    if cur_orbit == dest_orbit:
        first = "up" if cur_sat > dest_sat else "down"
    elif cur_sat != opt_line:
        first = "up" if cur_sat > opt_line else "down"
        second = "left" if cur_orbit > dest_orbit else "right"
    else:  # sat on optimal line
        first = "left" if cur_orbit > dest_orbit else "right"
        second = "up" if src_sat >= dest_sat else "down"

    return first, second


def get_direction(cur_orbit, dest_orbit, src_orbit, cur_sat, dest_sat, src_sat, opt_line):
    if cur_orbit != dest_orbit and \
            ((cur_sat == opt_line) or (dest_sat <= cur_sat < opt_line) or (opt_line < cur_sat <= dest_sat)):
        # ((src_sat <= dest_sat < cur_sat) or (cur_sat < dest_sat <= src_sat)) or
        # ((dest_sat <= src_sat < cur_sat) or (cur_sat < src_sat <= dest_sat))):
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


def n_hop_flood(n, cur, dest):
    visited = [dest]
    flood_path = []
    queue = [cur]
    while n > 0:
        round_arr = []
        while len(queue) > 0:
            tar = queue.pop()
            if tar in visited:
                pass
            else:
                flood_path.append(tar)
                visited.append(tar)
                round_arr.append(tar)

        for node in round_arr:
            if n > 0:
                for d in ["up", "down", "left", "right"]:
                    queue.append(node.link[d])
        n -= 1

        for node in flood_path:
            if dest.id not in node.detourTable:
                node.detourTable.append(dest.id)

    return [flood_path, dest.id]


def dtdr(constellation, mhr, src_sat, src_orbit, dest_sat, dest_orbit, src, dest):
    # print(src.id, "to", dest.id)
    detour_log = []
    flooding_hop = 2
    opt_line = get_optimal_row_line(mhr, src_sat, dest_sat)
    path = []
    fail_info = []
    fail_history = []
    prev_dir = None
    count = 0
    ####### debugging print ########
    # print("===MHR===")
    # for i in mhr:
    #     for j in i:
    #         print(j.id, end=" ")
    #     print()
    dest_info = dest.get_llh_info()
    cur_sat, cur_orbit = src_sat, src_orbit
    try:
        while cur_sat != dest_sat or cur_orbit != dest_orbit:  # 경로의 마지막이 destination일 때까지
            # sleep(0.1)
            success = True
            path.append(mhr[cur_sat][cur_orbit])
            first_direction, second_direction = new_get_direction(cur_orbit, dest_orbit, cur_sat, dest_sat, src_sat,
                                                                  opt_line)
            cur_info = mhr[cur_sat][cur_orbit].get_llh_info()
            cur_id = mhr[cur_sat][cur_orbit].id
            # ####### debugging print ########
            # print("=====", mhr[cur_sat][cur_orbit].id, "=====")
            if second_direction is None:
                direction = first_direction
            else:
                if dest.id in mhr[cur_sat][cur_orbit].detourTable:
                    # detour table에 의한 라우팅
                    # ####### debugging print ########
                    # print(cur_id, "has a direction in its detour table!")
                    direction = second_direction
                    detour_log.append(mhr[cur_sat][cur_orbit].id)
                else:
                    # 일반 라우팅
                    direction = first_direction
                    if (prev_dir == "up" and direction == "down") or (prev_dir == "down" and direction == "up"):
                        direction = second_direction

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
                if cur_sat >= len(mhr) or cur_sat < 0:
                    mhr = extend_mhr(mhr, direction)
                    if direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
                        cur_sat += 1
                        src_sat += 1
                        dest_sat += 1
                        opt_line += 1
                # print("next hop is", mhr[cur_sat][cur_orbit].id)
                prev_dir = direction
            else:  # 실패
                # ####### debugging print ########
                # print("!!!!! Fail to transmit on", mhr[cur_sat][cur_orbit].id, "!!!!!")
                fail_s, fail_o = cur_sat, cur_orbit
                fail_history.append(mhr[cur_sat][cur_orbit].id)
                fail_pair = [mhr[cur_sat][cur_orbit]]
                if direction == "left":
                    fail_pair.append(mhr[cur_sat][cur_orbit].link["left"])
                else:
                    fail_pair.append(mhr[cur_sat][cur_orbit].link["right"])
                fail_info.append(fail_pair)
                fail_info[-1][0].should_notice_recovery = True

                if direction == second_direction:
                    if first_direction == "up":
                        direction = "down"
                    else:
                        direction = "up"
                else:
                    direction = second_direction
                dt = 1 if direction == "down" else -1
                if cur_sat + dt >= len(mhr) or cur_sat + dt < 0:
                    mhr = extend_mhr(mhr, direction)
                    if direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
                        cur_sat += 1
                        src_sat += 1
                        dest_sat += 1
                    # ####### debugging print ########
                    # print("extending mhr")
                    # print("===MHR===")
                    # for i in mhr:
                    #     for j in i:
                    #         print(j.id, end=" ")
                    #     print()
                fail_info[-1][0].fail_experiences[0 if direction == "left" else 1].append(
                    n_hop_flood(flooding_hop, mhr[fail_s][fail_o], dest)
                )
                cur_sat += dt
                prev_dir = "up" if dt < 0 else "down"
                # ####### debugging print ########
                # print("move instantly to", mhr[cur_sat][cur_orbit].id)
            count += 1
            if len(mhr) >= 50:
                print(f'infinity loop on [{src.id} to {dest.id}]')
                print(f'mhr vertical / horizontal: {len(mhr)} / {len(mhr[0])}')
                print(f'on routing [{src.id} to {dest.id}]')
                print(f'src / dst: {src_sat},{src_orbit} / {dest_sat},{dest_orbit}')
                print(f'cur_sat / cur_orbit: {cur_sat} / {cur_orbit}')
                print("===MHR===")
                for i in mhr:
                    for j in i:
                        print(j.id, end=" ")
                    print()
                print("===path===")
                for i in path:
                    print(i.id, end=" ")
                print()
                print("===detour log===")
                for i in detour_log:
                    print(i, end=" ")
                print()
                print(f'fail_history: {len(fail_history)}')
                break
    except IndexError:
        print("Index Error==============================")
        print(f'mhr vertical / horizontal: {len(mhr)} / {len(mhr[0])}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'src / dst: {src_sat},{src_orbit} / {dest_sat},{dest_orbit}')
        print(f'cur_sat / cur_orbit: {cur_sat} / {cur_orbit}')
        print(f'fail_history: {fail_history}')
        print(f'path: {path}')
    path.append(mhr[cur_sat][cur_orbit])

    overhead_signal = 0
    for i in range(flooding_hop):
        overhead_signal += 3 ** i
    overhead_signal *= len(fail_info)

    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_info, overhead_signal


def constellation_to_array(matrix):
    num_rows = len(matrix)
    num_cols = len(matrix[0])

    rotated_matrix = []
    for col in range(num_cols - 1, -1, -1):
        new_row = []
        for row in range(num_rows):
            new_row.append(matrix[row][col])
        rotated_matrix.append(new_row)

    return rotated_matrix


def is_available(constellation, routing_table, s_orbit, d_orbit, check_line, opt_orbit_direction):
    do = opt_orbit_direction
    orbit_num = len(constellation[check_line])
    temp_orbit = s_orbit
    while True:
        if constellation[check_line][temp_orbit].id in routing_table:
            return False
        if temp_orbit == d_orbit:
            break
        temp_orbit += do
        temp_orbit = orbit_num - 1 if temp_orbit < 0 else temp_orbit % orbit_num
    return True


def best_direction(start, end, sat_num):
    if end >= start:
        plus_distance = end - start
    else:
        plus_distance = sat_num - start + end
    # 반시계 방향(-1)으로 이동
    if start >= end:
        minus_distance = start - end
    else:
        minus_distance = start + sat_num - end
    # 가장 짧은 경로 방향을 결정
    if minus_distance < plus_distance:
        return -1
    else:
        return 1


def optimal_line(constellation, routing_table, s_sat, s_orbit, d_sat, d_orbit):
    opt_line = s_sat
    opt_lat = latitude_convert(constellation[opt_line][0].get_llh_info()["lat"])
    opt_sat_direction = best_direction(s_sat, d_sat, len(constellation))
    opt_orbit_direction = best_direction(s_orbit, d_orbit, len(constellation[0]))
    ds = opt_sat_direction
    temp_line = s_sat + ds
    temp_line = len(constellation) - 1 if temp_line < 0 else temp_line % len(constellation)
    if s_sat == d_sat:
        opt_line = s_sat
    while True:
        temp_lat = latitude_convert(constellation[temp_line][0].get_llh_info()["lat"])
        if abs(opt_lat) < abs(temp_lat):
            opt_lat = temp_lat
            opt_line = temp_line
        if temp_line == d_sat:
            break
        temp_line += ds
        temp_line = len(constellation) - 1 if temp_line < 0 else temp_line % len(constellation)
    # 새로운 opt line 찾아야함
    if not is_available(constellation, routing_table, s_orbit, d_orbit, opt_line, opt_orbit_direction):
        return find_next_opt_line(constellation, routing_table, s_sat, s_orbit, d_sat, d_orbit, opt_line,
                                  opt_orbit_direction, opt_sat_direction)

    return opt_line, opt_orbit_direction, opt_sat_direction


def find_next_opt_line(constellation, routing_table, s_sat, s_orbit, d_sat, d_orbit, fail_line, opt_orbit_direction,
                       opt_sat_direction):
    up, down = -1, 1
    up_hop_waste, down_hop_waste = 0, 0
    upper_line, lower_line = fail_line, fail_line
    exceed = True if fail_line == d_sat else False
    while not is_available(constellation, routing_table, s_orbit, d_orbit, upper_line, opt_orbit_direction):
        upper_line += up
        upper_line = len(constellation) - 1 if upper_line < 0 else upper_line % len(constellation)
        if opt_sat_direction != up or exceed:
            up_hop_waste += 1
        if upper_line == d_sat:
            exceed = True
    exceed = True if fail_line == d_sat else False
    while not is_available(constellation, routing_table, s_orbit, d_orbit, lower_line, opt_orbit_direction):
        lower_line += down
        lower_line = len(constellation) - 1 if lower_line < 0 else lower_line % len(constellation)
        if opt_sat_direction != down or exceed:
            down_hop_waste += 1
        if lower_line == d_sat:
            exceed = True
    if up_hop_waste == down_hop_waste:
        if latitude_convert(constellation[upper_line][0].get_llh_info()["lat"]) < latitude_convert(
                constellation[lower_line][0].get_llh_info()["lat"]):
            opt_line = lower_line
        else:
            opt_line = upper_line
    elif up_hop_waste < down_hop_waste:
        opt_line = upper_line
    else:
        opt_line = lower_line
    new_sat_direction = best_direction(s_sat, opt_line, len(constellation))

    return opt_line, opt_orbit_direction, new_sat_direction


def ospf(constellation, routing_table, s_sat, s_orbit, dst_sat, dst_orbit):
    path = []
    fail_info = []
    opt_line, orbit_dir, sat_dir, count = optimal_line(constellation, routing_table, s_sat, s_orbit, dst_sat, dst_orbit)
    cur_s, cur_o = s_sat, s_orbit
    sat_num, orbit_num = len(constellation), len(constellation[0])
    print(f'src: {constellation[s_sat][s_orbit].id}, dst: {constellation[dst_sat][dst_orbit].id}')
    # print(f'in array src: {s_orbit}-{s_sat}, dst: {dst_orbit}-{dst_sat}')
    # print(f'orbit_dir: {orbit_dir}, sat_dir: {sat_dir}, opt_line: {opt_line}')
    re = False

    while True:
        # sleep(0.2)
        if not re:
            # print(f'current sat: {constellation[cur_s][cur_o].id}')
            # print(f'=================current in array: {cur_o}-{cur_s}=====================')
            path.append(constellation[cur_s][cur_o])
        else:
            re = False
        if cur_s == dst_sat and cur_o == dst_orbit:
            break
            # intra-ISL
        if cur_s != opt_line or cur_o == dst_orbit:
            cur_s += sat_dir
            cur_s = sat_num - 1 if cur_s < 0 else cur_s % sat_num
            # inter-ISL
        elif cur_s == opt_line:
            # inter-ISL success
            if constellation[cur_s][cur_o].link_state[0 if orbit_dir == -1 else 1] == 1:
                cur_o += orbit_dir
                cur_o = orbit_num - 1 if cur_o < 0 else cur_o % orbit_num
                if cur_o == dst_orbit:
                    sat_dir = best_direction(cur_s, dst_sat, sat_num)
            # inter-ISL fail
            else:
                # print('fail')
                routing_table.append(constellation[cur_s][cur_o].id)
                fail_info = [constellation[cur_s][cur_o], constellation[cur_s]]
                opt_line, orbit_dir, sat_dir, count = find_next_opt_line(constellation, routing_table, s_orbit, dst_sat,
                                                                         dst_orbit, opt_line, orbit_dir, sat_dir)
                # print(f'new orbit_dir: {orbit_dir}, new sat_dir: {sat_dir}, new opt_line: {opt_line}')
                re = True
                continue

    # 경로 리턴 path <List<Satellite>>, fail_info => [[에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>][flooding path]]
    return path, fail_info, routing_table, 0


def opspf(constellation, routing_table, s_sat, s_orbit, dst_sat, dst_orbit):
    path = []
    fail_info = []
    fail_count = 0
    opt_line, orbit_dir, sat_dir = optimal_line(constellation, routing_table, s_sat, s_orbit, dst_sat, dst_orbit)
    cur_s, cur_o = s_sat, s_orbit
    sat_num, orbit_num = len(constellation), len(constellation[0])
    # print(f'src: {constellation[s_sat][s_orbit].id}, dst: {constellation[dst_sat][dst_orbit].id}')
    # print(f'in array src: {s_orbit}-{s_sat}, dst: {dst_orbit}-{dst_sat}')
    # print(f'orbit_dir: {orbit_dir}, sat_dir: {sat_dir}, opt_line: {opt_line}')
    re = False

    while True:
        # sleep(0.2)
        if not re:
            # print(f'current sat: {constellation[cur_s][cur_o].id}')
            # print(f'=================current in array: {cur_o}-{cur_s}=====================')
            path.append(constellation[cur_s][cur_o])
        else:
            re = False
        if cur_s == dst_sat and cur_o == dst_orbit:
            break
            # intra-ISL
        if cur_s != opt_line or cur_o == dst_orbit:
            cur_s += sat_dir
            cur_s = sat_num - 1 if cur_s < 0 else cur_s % sat_num
            # inter-ISL
        elif cur_s == opt_line:
            # inter-ISL success
            if constellation[cur_s][cur_o].link_state[0 if orbit_dir == -1 else 1] == 1:
                cur_o += orbit_dir
                cur_o = orbit_num - 1 if cur_o < 0 else cur_o % orbit_num
                if cur_o == dst_orbit:
                    sat_dir = best_direction(cur_s, dst_sat, sat_num)
            # inter-ISL fail
            else:
                # print('fail')
                routing_table.append(constellation[cur_s][cur_o].id)
                fail_count += 1
                fail_info.append([constellation[cur_s][cur_o], constellation[cur_s][cur_o]])
                opt_line, orbit_dir, sat_dir = find_next_opt_line(constellation, routing_table, s_sat, s_orbit, dst_sat,
                                                                  dst_orbit, opt_line, orbit_dir, sat_dir)
                # print(f'new orbit_dir: {orbit_dir}, new sat_dir: {sat_dir}, new opt_line: {opt_line}')
                re = True
                continue
    overhead_signal = fail_count * sat_num * orbit_num * 3

    # 경로 리턴 path <List<Satellite>>, fail_info => [[에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>][flooding path]]
    return path, fail_info, routing_table, overhead_signal
