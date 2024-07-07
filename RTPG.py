import math

from parameter import DELTA_PI, DELTA_OMEGA, S_NUM, O_NUM, PHASING_PARAMETER, G_SEARCH_REGION_RADIUS, CONST_EARTH_RADIUS


def minimum_hop_estimate(src, dst):
    pi = math.pi
    p_s, p_d, r_s, r_d = src.p, dst.p, src.r, dst.r
    print("src:", p_s, r_s)
    print("dst:", p_d, r_d)

    left, right = (p_s-p_d+O_NUM) % O_NUM, (p_d-p_s+O_NUM) % O_NUM
    print(left, right)
    if left < right:
        horizontal = -1*left
    else:
        horizontal = right
    sum_of_delta_f = math.radians((360*(PHASING_PARAMETER / (S_NUM*O_NUM))) * horizontal)
    u_after_horizontal_move = src.true_anomaly+sum_of_delta_f if src.true_anomaly+sum_of_delta_f >= pi/2 else src.true_anomaly+sum_of_delta_f+(pi*2)
    r_after_horizontal_move = int((u_after_horizontal_move - pi/2)//DELTA_PI)
    print(r_after_horizontal_move)
    up, down = ((r_d-r_after_horizontal_move)+S_NUM) % S_NUM, ((r_after_horizontal_move-r_d)+S_NUM) % S_NUM
    print(up, down)
    if up <= down:
        vertical = up
    else:
        vertical = -1*down

    return horizontal, vertical

def coordinates_of_ground_station(lat, lon, inc):
    pi = math.pi
    u_ascending = math.asin(math.sin(lat)/math.sin(inc))
    u_descending = (lat/abs(lat))*pi - u_ascending

    ksi_asc = math.atan(math.cos(inc)*math.tan(u_ascending))
    ksi_desc = math.atan(math.cos(inc)*math.tan(u_descending)) + pi

    virtual_long_asc = (lon - ksi_asc + 2*pi) % (2*pi)
    virtual_long_desc = (lon - ksi_desc + 2*pi) % (2*pi)

    p_asc = virtual_long_asc//DELTA_OMEGA
    p_desc = virtual_long_desc//DELTA_OMEGA

    capital_u_asc = u_ascending if u_descending >= pi/2 else u_descending + 2*pi
    capital_u_desc = u_descending if u_descending >= pi/2 else u_descending + 2*pi

    r_asc = (capital_u_asc - pi/2)//DELTA_PI
    r_desc = (capital_u_desc - pi/2)//DELTA_PI

    return p_asc, r_asc, p_desc, r_desc

def grid_search_region(lat, lon, inc):
    pi = math.pi

    delta_p = 2*math.ceil((G_SEARCH_REGION_RADIUS)/(CONST_EARTH_RADIUS*math.cos(lat)*DELTA_OMEGA))

    h_min = inc - math.asin(math.sin(inc) * math.sin(pi / 2 - 2 * pi / S_NUM * (S_NUM - 1)))
    delta_r = 2*math.ceil((G_SEARCH_REGION_RADIUS)/(CONST_EARTH_RADIUS*h_min))

    return delta_p, delta_r
