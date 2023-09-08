import math

MAX_DIST = 10


# TODO
# 현재: 점들 주어진 상황에서 최대 통신 거리에 따라서 가능한 점들 중 minimum deflection angle을 선택 가능
# ex) MAX_DIST를 10에서 100으로 변경하면 더 멀리 있는 많은 점들을 고려할 수 있고, 실제로 next hop이 (3,4,5)에서 (7,8,9)로 변경됨.
# 해야할 일: 라우팅 진행 중 변하는 '현재 노드'의 minimum deflection angle을 계산하고 next hop을 결정할 수 있어야 함.


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


def get_euc_distance(A, B):
    return math.dist(A, B)


def max_dist_condition(A, B, maxd):
    return get_euc_distance(A, B) < maxd

#
# src = (0, 0, 0)
# dst = (10, 10, 10)
#
# points = [
#     (7, 8, 9),
#     (-1, -2, -3),
#     (10, 0, 5),
#     (3, 4, 5),
#     (6, 7, 8),
# ]


def get_proper(src, dest, available_list):
    smallest_angle = float('inf')
    index_of_point_with_smallest_angle = None

    vector = calculate_vector(src, dest)

    for i in range(len(available_list)):
        # if max_dist_condition(src, point):
        vector2 = calculate_vector(src, available_list[i])
        angle = calculate_angle(vector, vector2)

        if angle < smallest_angle:
            smallest_angle = angle
            index_of_point_with_smallest_angle = i

    return index_of_point_with_smallest_angle

# print(f"The point with the smallest angle to the vector is {point_with_smallest_angle} with an angle of {smallest_angle} degrees.")
