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

