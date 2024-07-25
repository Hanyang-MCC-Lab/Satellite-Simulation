from math import radians, degrees

from RTPG import coordinates_of_ground_station, grid_search_region
from parameter import CONST_EARTH_RADIUS, G_SEARCH_REGION_RADIUS, O_NUM, S_NUM
from util import update_ECEF_using_lat_lon, calculate_distance_s_to_g


class GroundStation:
    def __init__(self, geo_info, inclination):
        self.latitude = radians(geo_info[0])
        self.longitude = radians(geo_info[1])
        self.x, self.y, self.z = update_ECEF_using_lat_lon(self.latitude, self.longitude, CONST_EARTH_RADIUS)
        self.p_asc, self.r_asc, self.p_desc, self.r_desc = coordinates_of_ground_station(self.latitude, self.longitude,
                                                                                         inclination)
        self.delta_p, self.delta_r = grid_search_region(self.latitude, self.longitude, inclination)
        self.search_range_asc, self.search_range_desc = self.update_search_range()
        self.id = f'GS|a{self.p_asc}-{self.r_asc}|d{self.p_desc}-{self.r_desc}'
        self.connections = []
        self.routing_table = {}

    def get_ecef_info(self):
        return [self.x, self.y, self.z]

    def print_GS_info(self):
        print("=========")
        print("name:", self.id)
        print("latitude:", degrees(self.latitude))
        print("longitude:", degrees(self.longitude))
        print("p and r (asc):", self.p_asc, self.r_asc)
        print("p and r (desc):", self.p_desc, self.r_desc)
        print("delta_p:", self.delta_p)
        print("delta_r:", self.delta_r)
        print("connection:", len(self.connections))

    def connect_satellites(self, constellation):
        # print("ground_station:", self.name)
        [horizontal_range_asc, vertical_range_asc] = self.search_range_asc
        [horizontal_range_desc, vertical_range_desc] = self.search_range_desc
        for p in (horizontal_range_asc + horizontal_range_desc):
            for sat in constellation[p].satellites:
                radius = calculate_distance_s_to_g(self.latitude, self.longitude, sat.latitude, sat.longitude)
                # print(elevation)
                if radius <= G_SEARCH_REGION_RADIUS:
                    # print(radius)
                    if self not in sat.link["ground"]:
                        sat.link["ground"].append(self)
                    if sat not in self.connections:
                        self.connections.append(sat)
                    # ground station link attr
                    # sat.sphere_attr.radius = 70

    def reset_connections(self):
        for s in self.connections:
            s.link["ground"].remove(self)

        self.connections.clear()

    def update_search_range(self):
        search_area_asc, search_area_desc = [], []
        area_left_bound_asc, area_left_bound_desc = int((self.p_asc - self.delta_p / 2 + O_NUM) % O_NUM), int(
            (self.p_desc - self.delta_p / 2 + O_NUM) % O_NUM)
        area_right_bound_asc, area_right_bound_desc = int((self.p_asc + self.delta_p / 2) % O_NUM), int(
            (self.p_desc + self.delta_p / 2) % O_NUM)
        area_upper_bound_asc, area_upper_bound_desc = int((self.r_asc + self.delta_r / 2) % S_NUM), int(
            (self.r_desc + self.delta_r / 2) % S_NUM)
        area_lower_bound_asc, area_lower_bound_desc = int((self.r_asc - self.delta_r / 2 + S_NUM) % S_NUM), int(
            (self.r_desc - self.delta_r / 2 + S_NUM) % S_NUM)

        if area_left_bound_asc < area_right_bound_asc:
            search_area_asc.append(list(range(area_left_bound_asc, area_right_bound_asc + 1)))
        else:
            search_area_asc.append(list(range(area_left_bound_asc, O_NUM)) + list(range(0, area_right_bound_asc + 1)))
        if area_left_bound_desc < area_right_bound_desc:
            search_area_desc.append(list(range(area_left_bound_desc, area_right_bound_desc + 1)))
        else:
            search_area_desc.append(
                list(range(area_right_bound_desc, O_NUM)) + list(range(0, area_right_bound_desc + 1)))

        if area_upper_bound_asc > area_lower_bound_asc:
            search_area_asc.append(list(range(area_lower_bound_asc, area_upper_bound_asc + 1)))
        else:
            search_area_asc.append(list(range(area_upper_bound_asc, S_NUM)) + list(range(0, area_lower_bound_asc + 1)))
        if area_upper_bound_desc > area_lower_bound_desc:
            search_area_desc.append(list(range(area_lower_bound_desc, area_upper_bound_desc + 1)))
        else:
            search_area_desc.append(
                list(range(area_upper_bound_desc, S_NUM)) + list(range(0, area_lower_bound_desc + 1)))

        return search_area_asc, search_area_desc