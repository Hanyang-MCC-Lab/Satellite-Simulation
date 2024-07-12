import heapq
import math


def get_euc_distance(node_A, node_B):
    node_A_ecef = node_A.get_ecef_info()
    node_B_ecef = node_B.get_ecef_info()
    return math.dist(node_A_ecef, node_B_ecef)


def get_grid(mhr):
    grid = []
    satnum = len(mhr)
    orbnum = len(mhr[0])
    for s in range(len(mhr)):
        grid_row = []
        for o in range(len(mhr[0])):
            sat_distance = []
            if s != 0:
                sat_distance.append({'up': grid[s - 1][o]['down']})
            if s != satnum:
                sat_distance.append({'down': get_euc_distance(mhr[s][o], mhr[s + 1][o])})
            if o != 0:
                sat_distance.append({'left': grid_row[o - 1]['right']})
            if o != orbnum:
                sat_distance.append({'right': get_euc_distance(mhr[s][o], mhr[s][o + 1])})
            grid_row.append(sat_distance)
        grid.append(grid_row)
    return grid


def dijkstra(grid, start, target):
    rows, cols = len(grid), len(grid[0])
    directions = {
        'right': (0, 1),
        'left': (0, -1),
        'down': (1, 0),
        'up': (-1, 0)
    }
    min_heap = [(0, start)]
    visited = set()
    distances = [[float('inf')] * cols for _ in range(rows)]
    parents = {start: None}
    sx, sy = start
    distances[sx][sy] = 0

    while min_heap:
        dist, (x, y) = heapq.heappop(min_heap)
        if (x, y) in visited:
            continue
        if (x, y) == target:
            return dist, reconstruct_path(parents, target)
        visited.add((x, y))

        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and direction in grid[x][y]:
                new_dist = dist + grid[x][y][direction]
                if new_dist < distances[nx][ny]:
                    distances[nx][ny] = new_dist
                    parents[(nx, ny)] = (x, y)
                    heapq.heappush(min_heap, (new_dist, (nx, ny)))

    return float('inf'), []


def reconstruct_path(parents, target):
    path = []
    step = target
    while step is not None:
        path.append(step)
        step = parents[step]
    path.reverse()
    return path


import math

# SAT_NUM과 ORBIT_NUM 정의
SAT_NUM = 5
ORBIT_NUM = 5

# detour_table 초기화
detour_table = {f'SAT-{j}-{i}': set() for i in range(ORBIT_NUM) for j in range(SAT_NUM)}


# 노드 클래스 예제
class Node:
    def __init__(self, id):
        self.id = id


# 예제 사용 방법
if __name__ == "__main__":
    # 노드 초기화
    cur = Node('SAT-1-2')
    d_id = 'example_id'
    detour_table = {}
    detour_table[cur.id] = set()
    # 값 추가
    detour_table[cur.id].add(d_id)

    # 값 확인
    if d_id in detour_table[cur.id]:
        print(f"{d_id} is in detour_table at {cur.id}")
    else:
        print(f"{d_id} is not in detour_table at {cur.id}")

    # 값 제거
    detour_table[cur.id].discard(d_id)

    # 값 제거 후 확인
    if d_id in detour_table[cur.id]:
        print(f"{d_id} is still in detour_table at {cur.id}")
    else:
        print(f"{d_id} has been removed from detour_table at {cur.id}")

# Example values
# theta = 25  # in degrees
# h = 550  # in km (altitude of the satellite)
# r_e = 6371  # in km (radius of the Earth)

# beta, gamma = calculate_beta_and_gamma(theta, h, r_e)
# print("Gamma:", gamma)
# print("Beta:", beta)
# print("R_s:", beta*r_e)
