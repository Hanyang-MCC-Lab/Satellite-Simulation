import math

from parameter import DELTA_PI, DELTA_OMEGA, S_NUM, O_NUM


def minimum_hop_estimate(src, dst):
    pi = math.pi
    p_s, p_d, r_s, r_d = src.p, dst.p, src.r, dst.r

    left, right = (p_s-p_d+S_NUM) % S_NUM, (p_d-p_s+S_NUM) % S_NUM
    if left < right:
        horizontal = -1*left
    else:
        horizontal = right
    delta_f = DELTA_PI * horizontal
    lat_variation = ((src.latitude + delta_f)-(pi/2))
    R_after_horizontal_move = (lat_variation-(pi/2))//S_NUM if lat_variation >= pi/2 else (lat_variation+(1.5*pi))//S_NUM

    up, down = (O_NUM+(r_d-R_after_horizontal_move))//O_NUM, (O_NUM-(r_d-R_after_horizontal_move))//O_NUM
    if up <= down:
        vertical = up
    else:
        vertical = -1*down

    return horizontal, vertical
