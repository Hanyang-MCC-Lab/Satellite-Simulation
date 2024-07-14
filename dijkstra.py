from math import dist
import heapq


def build_link_state_database(nodes, routing_table):
    lsdb = {}
    for row in nodes:
        for node in row:
            n_id = node.id
            lsdb[n_id] = {}
            if routing_table[n_id][0]:
                lsdb[n_id][node.link["left"].id] = (dist(node.get_ecef_info(), node.link["left"].get_ecef_info()), "left")
            else:
                lsdb[n_id][node.link["left"].id] = (float('inf'), "left")
            if routing_table[n_id][1]:
                lsdb[n_id][node.link["right"].id] = (dist(node.get_ecef_info(), node.link["right"].get_ecef_info()), "right")
            else:
                lsdb[n_id][node.link["right"].id] = (float('inf'), "right")
            lsdb[n_id][node.link["up"].id] = (dist(node.get_ecef_info(), node.link["up"].get_ecef_info()), "up")
            lsdb[n_id][node.link["down"].id] = (dist(node.get_ecef_info(), node.link["down"].get_ecef_info()), "down")

    return lsdb


def dijkstra(lsdb, start):
    distances = {node: float('inf') for node in lsdb}
    distances[start] = 0
    priority_queue = [(0, start)]
    previous_nodes = {node: (None, None) for node in lsdb}  # (previous_node, direction)

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, (weight, direction) in lsdb[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = (current_node, direction)
                heapq.heappush(priority_queue, (distance, neighbor))

    return previous_nodes

def shortest_path(previous_nodes, start, end):
    # print(previous_nodes)
    path = []
    directions = []
    current_node = end
    while current_node != start:
        if current_node is None:
            return None, None
        path.insert(0, current_node)
        # print(current_node)
        prev_node, direction = previous_nodes[current_node]
        directions.insert(0, direction)
        current_node = prev_node
    path.insert(0, start)
    return path, directions
