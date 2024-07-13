
import random
from time import sleep
from RTPG import minimum_hop_estimate
from math import sqrt, acos, degrees, radians, sin, cos, atan2
from vpython import vec, color


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


# def distributed_detour_routing(constellation, detour_table, src_sat, src_orbit, dest_sat, dest_orbit, src, dest):
#     # print(src.id, "to", dest.id)
#     opt_line = new_get_direction(src.r,)get_optimal_row_line(mhr, src_sat, dest_sat)
#     need_flood = False
#     path = []
#     fail_info = []
#     fail_history = []
#     overhead_signal = 0
#     # print("===MHR===")
#     # for i in mhr:
#     #     for j in i:
#     #         print(j.id, end=" ")
#     #     print()
#     # print("length", len(mhr))
#     dest_info = dest.get_llh_info()
#     cur_sat, cur_orbit = src_sat, src_orbit
#     while cur_sat != dest_sat or cur_orbit != dest_orbit:  # 경로의 마지막이 destination일 때까지
#         # sleep(0.1)
#         success = True
#         path.append(mhr[cur_sat][cur_orbit])
#         cur_info = mhr[cur_sat][cur_orbit].get_llh_info()
#         cur_id = mhr[cur_sat][cur_orbit].id
#         first_direction, second_direction = new_get_direction(cur_orbit, dest_orbit, cur_sat, dest_sat, src_sat,
#                                                               opt_line)
#         # print("=====", mhr[cur_sat][cur_orbit].id, "=====")
#         # print("cur_sat", cur_sat, "cur_orbit", cur_orbit)
#         # print("current:", cur_sat, cur_orbit)
#         if second_direction is None:
#             direction = first_direction
#         else:
#             if dest.id in detour_table[(cur_sat, cur_orbit)]:
#                 # detour table에 의한 라우팅
#                 # ####### debugging print ########
#                 # print(cur_id, "has a direction in its detour table!")
#                 direction = second_direction
#             else:
#                 # 일반 라우팅
#                 direction = first_direction
#                 if (prev_dir == "up" and direction == "down") or (prev_dir == "down" and direction == "up"):
#                     direction = second_direction
#
#             if (direction == "left" and mhr[cur_sat][cur_orbit].link_state[0] == 0) or (
#                     direction == "right" and mhr[cur_sat][cur_orbit].link_state[1] == 0):
#                 success = False
#             else:
#                 success = True
#
#             if need_flood:
#                 flood_return = selective_flood(mhr, src_sat, src_orbit, cur_sat, cur_orbit, dest, direction)
#                 overhead_signal += len(flood_return[0])
#                 fail_info[-1][0].fail_experiences[0 if direction == "left" else 1].append(flood_return)
#                 need_flood = False
#
#         # step2. 성공/실패에 따른 알고리즘 분리
#         if success:  # 성공
#             if direction == "up":
#                 cur_sat -= 1
#             elif direction == "down":
#                 cur_sat += 1
#             elif direction == "left":
#                 cur_orbit -= 1
#             else:  # direction == "right"
#                 cur_orbit += 1
#
#             prev_dir = direction
#         else:  # 실패
#             # print("!!!!! Fail to transmit on", mhr[cur_sat][cur_orbit].id, "!!!!!")
#             need_flood = True
#             fail_history.append((cur_sat, cur_orbit))
#             fail_pair = [mhr[cur_sat][cur_orbit]]
#
#             if direction == "left":
#                 fail_pair.append(mhr[cur_sat][cur_orbit - 1])
#             else:
#                 fail_pair.append(mhr[cur_sat][cur_orbit + 1])
#             fail_info.append(fail_pair)
#             fail_pair[-1].should_notice_recovery = True
#
#             direction = second_direction
#             cur_sat += 1 if direction == "down" else -1
#
#             if cur_sat >= len(mhr) or cur_sat < 0:
#                 mhr = extend_mhr(mhr, direction)
#                 if direction == "up":  # 위로 확장됨에 따른 src_sat, dest_sat, fail_sat 수정
#                     cur_sat += 1
#                     src_sat += 1
#                     dest_sat += 1
#                 # opt_line = cur_sat
#                 # print("extending mhr")
#                 # print("===MHR===")
#                 # print(mhr)
#                 # for i in mhr:
#                 #     for j in i:
#                 #         print(j.id, end=" ")
#                 #     print()
#             # print("move instantly to", mhr[cur_sat][cur_orbit].id)
#     path.append(mhr[cur_sat][cur_orbit])
#
#     # 경로 리턴 path <List<Satellite>>, fail_info => [에러 발생 위성<Satellite>, 원래 도착 지점<Satellite>]
#     return path, fail_info, overhead_signal, detour_table
    # return path


def selective_flood(detour_table, src_sat, src_orbit, fail_sat, fail_orbit, destination, sec_direction):
    # 진행 경우, 1. inter-intra, 2. intra-inter, 3. intra-inter-intra
    # print(sec_direction)
    flood_path = []
    d_id = destination.id
    flood_direction = {"down": (-1, 0), "up": (1, 0), "right": (0, -1), "left": (0, 1)}
    csat, corb = fail_sat, fail_orbit
    dsat, dorb = flood_direction[sec_direction]
    #
    # detour_table[(csat, corb)].add(d_id)
    # flood_path.append(mhr[csat][corb])
    # while csat != src_sat and corb != src_orbit:
    #     csat, corb = csat + dsat, corb + dorb
    #     try:
    #         mhr[csat][corb].detourTable.add(d_id)
    #     except IndexError:
    #         print(f'detour point: {fail_sat}, {fail_orbit} sec_direction: {sec_direction}')
    #         print(f'index error: {csat}, {corb}')
    #         print("===MHR===")
    #         print(mhr)
    #         for i in mhr:
    #             for j in i:
    #                 print(j.id, end=" ")
    #             print()
    #     flood_path.append(mhr[csat][corb])

    # print("flood path: ", end="")
    # for fsat in flood_path:
    #     print(fsat.id, end=" ")
    # print()

    return [flood_path, destination.id]


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
    src, dest = region[src_r][src_p], region[dest_r][dest_p]
    r_num, p_num = len(region), len(region[0])
    ####### debugging print ########
    print(src.id, "to", dest.id)
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
            sleep(0.1)
            print("=====", cur.id, "=====")
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
                    print("======detour=======")

            if (direction == "left" and cur.link_state[0] == 0) or (direction == "right" and cur.link_state[1] == 0):
                print("*******failure*******")
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


    except IndexError:
        print("Index Error==============================")
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'rest vertical / horizontal: {vertical} / {horizontal}')
        print(f'on routing [{src.id} to {dest.id}]')
        print(f'src / dst: {src.id} / {dest.id}')
        print(f'path: {path}')

    overhead_signal = 0
    for i in range(flooding_hop):
        overhead_signal += 3 ** i
    overhead_signal *= fail_count
    print("done==============================")
    print(f'rest vertical / horizontal: {vertical} / {horizontal}')
    print(f'on routing [{src.id} to {dest.id}]')
    print(f'hops: {len(path)}')
    print(f'fail counts: {fail_count}')
    print(f'path:', '-'.join(sat.id for sat in path))
    print("=================================")

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
