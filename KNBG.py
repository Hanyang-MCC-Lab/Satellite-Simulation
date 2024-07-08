from parameter import S_NUM, O_NUM

class KeyNodeBasedGraph:
    def __init__(self, constellation, ground_stations):
        self.key_nodes = []
        self.weights = []
        self.graph = {}
        for g in ground_stations:
            for orbit in constellation:
                for satellite in orbit.satellites:
                    is_in_area = in_search_area(g, satellite)
                    if is_in_area == 0:
                        pass
                    else:
                        self.key_nodes.append(satellite)
                        satellite.link["ground"].append(g)
                        g.connections.append(satellite)
        for s1 in self.key_nodes:
            for s2 in self.key_nodes:
                if s1 == s2:
                    pass






def connect_sat_ground(constellation, ground_stations):
    # key_nodes = []
    for g in ground_stations:
        for orbit in constellation:
            for satellite in orbit.satellites:
                is_in_area = in_search_area(g, satellite)
                if is_in_area == 0:
                    pass
                else:
                    # key_nodes.append(satellite)
                    satellite.link["ground"].append(g)
                    g.connections.append(satellite)

def in_search_area(g, satellite):
    p_s, r_s = satellite.p, satellite.r
    p_g_asc, r_g_asc = g.p_asc, g.r_asc
    p_g_desc, r_g_desc = g.p_desc, g.r_desc
    delta_p, delta_r = g.delta_p, g.delta_r

    s_in_area_p_asc = min((p_g_asc-p_s+O_NUM)%O_NUM, (p_s-p_g_asc+O_NUM)%O_NUM) <= delta_p/2
    s_in_area_p_desc = min((p_g_desc-p_s+O_NUM)%O_NUM, (p_s-p_g_desc+O_NUM)%O_NUM) <= delta_p/2
    s_in_area_r_asc = min((r_g_asc-r_s+S_NUM)%S_NUM, (r_s-r_g_asc+S_NUM)%S_NUM) <= delta_r/2
    s_in_area_r_desc = min((r_g_desc-r_s+S_NUM)%S_NUM, (r_s-r_g_desc+S_NUM)%S_NUM) <= delta_r/2

    if s_in_area_r_asc and s_in_area_p_asc:
        return 1
    elif s_in_area_p_desc and s_in_area_r_desc:
        return -1
    else:
        return 0



    # area_left_bound_asc, area_left_bound_desc = (p_g_asc - delta_p/2 + S_NUM) % S_NUM, (p_g_desc - delta_p/2 + S_NUM) % S_NUM
    # area_right_bound_asc, area_right_bound_desc = (p_g_asc + delta_p/2) % S_NUM, (p_g_desc + delta_p/2) % S_NUM
    # area_upper_bound_asc, area_upper_bound_desc = (r_g_asc + delta_r/2) % O_NUM, (r_g_desc + delta_r/2) % O_NUM
    # area_lower_bound_asc, area_lower_bound_desc = (r_g_asc - delta_r/2 + O_NUM) % O_NUM, (r_g_desc - delta_r/2 + O_NUM) % O_NUM
    #
    # if area_left_bound_asc < area_right_bound_asc:
    #     search_area_asc.append(list(range(area_left_bound_asc, area_right_bound_asc+1)))
    # else:
    #     search_area_asc.append(list(range(area_left_bound_asc, S_NUM))+list(range(0, area_right_bound_asc+1)))
    # if area_left_bound_desc < area_right_bound_desc:
    #     search_area_desc.append(list(range(area_left_bound_desc, area_right_bound_desc+1)))
    # else:
    #     search_area_desc.append(list(range(area_lower_bound_desc, S_NUM))+list(range(0, area_right_bound_desc+1)))