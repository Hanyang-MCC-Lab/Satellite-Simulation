import heapq
import math

def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def dijkstra(nodes, edges, start):
    # 거리와 경로를 저장할 자료구조
    distances = {node: float('inf') for node in nodes}
    previous_nodes = {node: None for node in nodes}
    distances[start] = 0
    pq = [(0, start)]

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        # 더 짧은 경로가 있다면 스킵
        if current_distance > distances[current_node]:
            continue

        # 인접 노드 탐색
        for neighbor, weight in edges[current_node]:
            distance = current_distance + weight

            # 더 짧은 경로 발견 시 업데이트
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))

    return distances, previous_nodes

def construct_path(previous_nodes, end):
    path = []
    step = end
    while previous_nodes[step] is not None:
        path.append(step)
        step = previous_nodes[step]
    path.append(step)
    return path[::-1]

# 예제 위성 좌표
nodes = {
    'A': (0, 0, 0),
    'B': (1, 1, 1),
    'C': (2, 2, 2),
    'D': (1, 2, 2),
    'E': (2, 0, 1)
}

# 간선과 가중치(거리) 계산
edges = {
    node: [(other, euclidean_distance(pos, nodes[other]))
           for other in nodes if other != node]
    for node, pos in nodes.items()
}

# 시작점
start = 'A'
# 종점
end = 'D'

distances, previous_nodes = dijkstra(nodes, edges, start)
path = construct_path(previous_nodes, end)

print("Shortest Path:", path)
print("Total Distance:", distances[end])