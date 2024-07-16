
import random
from time import sleep
from RTPG import minimum_hop_estimate
from math import sqrt, acos, degrees, radians, sin, cos, atan2
from vpython import vec, color

from dijkstra import dijkstra, shortest_path, build_link_state_database


def latitude_convert(degree):
    if 90 < degree <= 270:
        return (degree - 180) * -1
    elif 270 < degree <= 360:
        return degree - 360
    else:
        return degree


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


def get_optimal_row_line(s_r, d_r, vertical):
    target_value = [0, 11, 12, 21]
    if s_r == d_r:
        return s_r
    if vertical > 0:
        if s_r < d_r:
            arr = list(range(s_r, d_r+1))
        else:
            arr = list(range(s_r, 22))+list(range(d_r+1))
    else:
        if s_r < d_r:
            arr = list(range(d_r, 22))+list(range(s_r+1))
        else:
            arr = list(range(d_r, s_r+1))
    optimal = min(arr, key=lambda x: min(abs(x-t) for t in target_value))

    return optimal


def distributed_detour_routing(region, detour_table, src_p, src_r, dest_p, dest_r):
    src, dest = region[src_p][src_r], region[dest_p][dest_r]
    # r_num, p_num = len(region[0]), len(region)
    ####### debugging print ########
    # print(src.id, "to", dest.id)
    d_id = dest.id
    overhead_signal = 0
    horizontal, vertical = minimum_hop_estimate(src, dest)
    first_direction = "inter" if abs(latitude_convert(src.latitude)) >= abs(latitude_convert(dest.latitude)) else "intra"
    initial_direction = "up" if vertical > 0 else "down"
    path = []
    fail_count = 0
    forever_inter = False
    cur = src
    try:
        while 1:  # 경로의 마지막이 destination일 때까지
            cur_p = cur.p
            path.append(cur)
            if cur.id == d_id:
                break
            ####### debugging print ########
            # sleep(0.1)
            # print("=====", cur.id, "=====")
            if cur_p == dest_p:
                if vertical < 0:
                    direction = "down"
                else:
                    direction = "up"
            elif forever_inter:
                if horizontal > 0:
                    direction = "right"
                else:
                    direction = "left"
            else:
                if first_direction == "intra": # 상향
                    if vertical != 0:
                        if vertical < 0:
                            direction = "down"
                        else:
                            direction = "up"
                    else:
                        if horizontal > 0:
                            direction = "right"
                        else:
                            direction = "left"
                else: # 하향
                    if horizontal != 0:
                        if horizontal > 0:
                            direction = "right"
                        else:
                            direction = "left"
                    else:
                        if vertical < 0:
                            direction = "down"
                        else:
                            direction = "up"

            if (cur_p != dest_p) and d_id in detour_table[cur.id]:
                    if horizontal > 0:
                        direction = "right"
                    else:
                        direction = "left"
                    # print("======detour=======")

            if (direction == "left" and cur.link_state[0] == 0) or (direction == "right" and cur.link_state[1] == 0):
                # print("*******failure*******")
                forever_inter = True
                direction = initial_direction
                f_direction = "down" if initial_direction == "up" else "up"
                flood_info, detour_table, overheads = selective_flood(detour_table, cur.link[f_direction], horizontal, src_p, d_id)
                cur.fail_experiences[0 if direction == "left" else 1].append(flood_info)
                fail_count += 1
                overhead_signal += overheads

            if direction == "up":
                vertical -= 1
            elif direction == "down":
                vertical += 1
            elif direction == "right":
                horizontal -= 1
            else:
                horizontal += 1
            cur = cur.link[direction]
            if len(path) > 10000:
                print("*******loop*******")
                print(f'rest vertical / horizontal: {vertical} / {horizontal}')
                print(f'on routing [{src.id} to {dest.id}]')
                print(f'fail count: {fail_count}')
                print(f'path:', '-'.join(sat.id for sat in path[-10:]))
                break
    except IndexError:
        print("Index Error==============================")
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'src / dst: {src.id} / {dest.id}')
        print(f'path:', '-'.join(sat.id for sat in path[-10:]))

    return path, fail_count, overhead_signal, detour_table

def selective_flood(detour_table, start_sat, horizontal, end_p, d_id):
    # 진행 경우, 1. inter-intra, 2. intra-inter, 3. intra-inter-intra
    # print(sec_direction)
    overhead_count = 0
    flood_dir = "left" if horizontal > 0 else "right"
    flood_path = []
    cur = start_sat
    while cur.p == end_p:
        flood_path.append(cur.id)
        cur = cur.link[flood_dir]
    flood_path.append(cur.id)

    for sat_id in flood_path:
        if d_id not in detour_table[sat_id]:
            overhead_count += 1
            detour_table[sat_id].add(d_id)

    return [flood_path, d_id], detour_table, overhead_count


def recovery_flood(sat, index, detour_table):
    for flood_path in sat.fail_experiences[index]:
        d_id = flood_path[1]
        for i in flood_path[0]:
            # print(dest, i.detourTable)
            detour_table[i].discard(d_id)
    return detour_table

def calculate_angle(vector1, vector2):
    dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
    magnitude1 = sqrt(sum(v1 ** 2 for v1 in vector1))
    magnitude2 = sqrt(sum(v2 ** 2 for v2 in vector2))
    cosine_similarity = dot_product / (magnitude1 * magnitude2)

    # Ensure the value is within the valid range for acos ([-1, 1])
    cosine_similarity = min(max(cosine_similarity, -1), 1)

    angle_in_radians = acos(cosine_similarity)
    angle_in_degrees = degrees(angle_in_radians)
    return angle_in_degrees


def new_get_direction(cur_r, vertical, horizontal, opt_line):
    first, second = None, None
    if horizontal == 0:
        first = "up" if vertical > 0 else "down"
    elif cur_r != opt_line:
        first = "up" if vertical > 0 else "down"
        second = "left" if horizontal < 0 else "right"
    else:  # sat on optimal line
        first = "left" if horizontal < 0 else "right"
        second = "up" if vertical > 0 else "down"

    return first, second


def n_hop_flood(n, cur, d_id, detour_table):
    visited = set()
    flood_path = []
    queue = [cur]
    while n > 0:
        round_arr = []
        while queue:
            tar = queue.pop(0)
            if tar not in visited:
                flood_path.append(tar.id)
                visited.add(tar)
                round_arr.extend(tar.link[d] for d in ["up", "down", "left", "right"])
        queue = round_arr
        n -= 1

        for id in flood_path:
            detour_table[id].add(d_id)

    return [flood_path, d_id], detour_table


def dtdr(region, detour_table, src_p, src_r, dest_p, dest_r):
    src, dest = region[src_p][src_r], region[dest_p][dest_r]
    r_num, p_num = len(region[0]), len(region)
    ####### debugging print ########
    # print(src.id, "to", dest.id)
    d_id = dest.id
    flooding_hop = 2
    horizontal, vertical = minimum_hop_estimate(src, dest)
    first_direction = "inter" if abs(latitude_convert(src.latitude)) >= abs(latitude_convert(dest.latitude)) else "intra"
    initial_direction = "up" if vertical > 0 else "down"
    path = []
    fail_count = 0
    forever_inter = False
    cur = src
    try:
        while 1:  # 경로의 마지막이 destination일 때까지
            cur_p = cur.p
            path.append(cur)
            if cur.id == d_id:
                break
            ####### debugging print ########
            # sleep(0.1)
            # print("=====", cur.id, "=====")
            if cur_p == dest_p:
                if vertical < 0:
                    direction = "down"
                else:
                    direction = "up"
            elif forever_inter:
                if horizontal > 0:
                    direction = "right"
                else:
                    direction = "left"
            else:
                if first_direction == "intra": # 상향
                    if vertical != 0:
                        if vertical < 0:
                            direction = "down"
                        else:
                            direction = "up"
                    else:
                        if horizontal > 0:
                            direction = "right"
                        else:
                            direction = "left"
                else: # 하향
                    if horizontal != 0:
                        if horizontal > 0:
                            direction = "right"
                        else:
                            direction = "left"
                    else:
                        if vertical < 0:
                            direction = "down"
                        else:
                            direction = "up"

            if (cur_p != dest_p) and d_id in detour_table[cur.id]:
                    if direction in ["up", "down"]:
                        if horizontal > 0:
                            direction = "right"
                        else:
                            direction = "left"
                    else:
                        direction = initial_direction
                        forever_inter = True
                    # print("======detour=======")

            if (direction == "left" and cur.link_state[0] == 0) or (direction == "right" and cur.link_state[1] == 0):
                # print("*******failure*******")
                forever_inter = True
                direction = initial_direction
                flood_info, detour_table = n_hop_flood(flooding_hop, cur, d_id, detour_table)
                cur.fail_experiences[0 if direction == "left" else 1].append(flood_info)
                fail_count += 1

            if direction == "up":
                vertical -= 1
            elif direction == "down":
                vertical += 1
            elif direction == "right":
                horizontal -= 1
            else:
                horizontal += 1
            cur = cur.link[direction]
            if len(path) > 10000:
                print("*******loop*******")
                print(f'rest vertical / horizontal: {vertical} / {horizontal}')
                print(f'on routing [{src.id} to {dest.id}]')
                print(f'fail count: {fail_count}')
                print(f'path:', '-'.join(sat.id for sat in path[-10:]))
                break
    except IndexError:
        print("Index Error==============================")
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'src / dst: {src.id} / {dest.id}')
        print(f'path:', '-'.join(sat.id for sat in path[-10:]))


    overhead_signal = 0
    for i in range(flooding_hop):
        overhead_signal += 3 ** i
    overhead_signal *= fail_count
    # print("done==============================")
    # print(f'rest vertical / horizontal: {vertical} / {horizontal}')
    # print(f'on routing [{src.id} to {dest.id}]')
    # print(f'hops: {len(path)}')
    # print(f'fail counts: {fail_count}')
    # print(f'path:', '-'.join(sat.id for sat in path))
    # print("=================================")

    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_count, overhead_signal, detour_table




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


def verify_path(path, directions):
    for i in range(len(path) - 1):
        current_node = path[i]
        direction = directions[i]
        # 링크가 끊겨있지 않은지 확인
        # print(f'current_node: {current_node.id}, direction: {direction}')
        # print(f'link: {current_node.link}')
        if direction in ["left", "right"]:
            if current_node.link_state[0 if direction == "left" else 1] == 0:
                return i
    return -1

def opspf(constellation, routing_table, src_id, dest_id):
    fail_count = 0
    overhead_signal = 0
    # sleep(0.2)
    lsdb = build_link_state_database(constellation, routing_table)
    previous_nodes = dijkstra(lsdb, src_id)
    path, directions = shortest_path(previous_nodes, src_id, dest_id)
    # print(f'path: {path}')
    # print(f'directions: {directions}')
    new_path = []
    for i in path:
        parts = i.split('-')
        o, s = int(parts[1]), int(parts[2])
        new_path.append(constellation[o][s])
    path = new_path

    fail_index = verify_path(path, directions)
    if fail_index == -1:
        overhead_signal = fail_count * 72 * 22 * 3
        return path, fail_count, routing_table, overhead_signal
    else:
        fail_count += 1
        fail_sat_id = path[fail_index].id
        # print("fail sat:", fail_sat_id)
        routing_table[fail_sat_id][0 if directions[fail_index] == 'left' else 1] = False
        r_path, r_fail_count, r_routing_table, r_overhead_signal = opspf(constellation, routing_table, fail_sat_id, dest_id)
        path = path[:fail_index] + r_path
        fail_count, routing_table, overhead_signal = fail_count+r_fail_count, r_routing_table, overhead_signal+r_overhead_signal
    # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
    return path, fail_count, routing_table, overhead_signal
