from math import radians, asin, pi, sin, atan, cos, tan

from parameter import DELTA_PI, DELTA_OMEGA, S_NUM, O_NUM, PHASING_PARAMETER, G_SEARCH_REGION_RADIUS, CONST_EARTH_RADIUS, EXTRA_P

class RTPG:
    def __init__(self):
        self.graph = []
        #only for 'refresh'
        self.new_graph = []

    def append_orbit(self, orbit):
        new_orbit = []
        s_num = len(orbit)
        start_index = 0
        for i in range(s_num):
            if orbit[i].r == 0:
                start_index = i
                break
        cur_index, done = start_index, False
        while not done:
            new_orbit.append(orbit[cur_index])
            cur_index = (cur_index+1) % s_num
            if cur_index == start_index:
                done = True
        self.graph.append(new_orbit)

    def refresh_rtpg(self):
        for orbit_i in range(O_NUM):
            for sat_i in range(S_NUM):
                if self.graph[orbit_i][sat_i].r == sat_i:
                    continue
                else:
                    self.graph[orbit_i] = shift_array(self.graph[orbit_i])



def shift_array(arr):
    return [arr[-1]]+arr[:-1]


def minimum_hop_estimate(src, dst):
    p_s, p_d, r_s, r_d = src.p, dst.p, src.r, dst.r
    # print("src:", p_s, r_s)
    # print("dst:", p_d, r_d)

    left, right = (p_s-p_d+O_NUM) % O_NUM, (p_d-p_s+O_NUM) % O_NUM
    # print(left, right)
    if left < right:
        horizontal = -1*left
    else:
        horizontal = right
    sum_of_delta_f = radians((360*(PHASING_PARAMETER / (S_NUM*O_NUM))) * horizontal)
    u_after_horizontal_move = src.true_anomaly+sum_of_delta_f if src.true_anomaly+sum_of_delta_f >= pi/2 else src.true_anomaly+sum_of_delta_f+(pi*2)
    r_after_horizontal_move = int((u_after_horizontal_move - pi/2)//DELTA_PI)
    # print(r_after_horizontal_move)
    up, down = ((r_d-r_after_horizontal_move)+S_NUM) % S_NUM, ((r_after_horizontal_move-r_d)+S_NUM) % S_NUM
    # print(up, down)
    if up <= down:
        vertical = up
    else:
        vertical = -1*down

    return horizontal, vertical

def coordinates_of_ground_station(lat, lon, inc):
    u_ascending = asin(sin(lat)/sin(inc))
    u_descending = (lat/abs(lat))*pi - u_ascending

    ksi_asc = atan(cos(inc)*tan(u_ascending))
    ksi_desc = atan(cos(inc)*tan(u_descending)) + pi

    virtual_long_asc = (lon - ksi_asc + 2*pi) % (2*pi)
    virtual_long_desc = (lon - ksi_desc + 2*pi) % (2*pi)

    p_asc = (round(virtual_long_asc//DELTA_OMEGA)+1) % O_NUM
    p_desc = (round(virtual_long_desc//DELTA_OMEGA)+1) % O_NUM

    capital_u_asc = u_ascending if u_ascending >= pi/2 else u_ascending + 2*pi
    capital_u_desc = u_descending if u_descending >= pi/2 else u_descending + 2*pi

    r_asc = (round((capital_u_asc - pi/2)/DELTA_PI)-1+S_NUM) % S_NUM
    r_desc = (round((capital_u_desc - pi/2)/DELTA_PI)-1+S_NUM) % S_NUM

    return int(p_asc), int(r_asc), int(p_desc), int(r_desc)

def grid_search_region(lat, lon, inc):

    delta_p = 2*round((G_SEARCH_REGION_RADIUS)/(CONST_EARTH_RADIUS*cos(lat)*DELTA_OMEGA)+EXTRA_P)

    h_min = inc - asin(sin(inc) * sin(pi / 2 - 2 * pi / S_NUM * (S_NUM - 1)))
    delta_r = 2*round((G_SEARCH_REGION_RADIUS)/(CONST_EARTH_RADIUS*h_min))

    return delta_p, delta_r
