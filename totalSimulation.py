import subprocess
import time
import concurrent.futures

from util import set_routing_simulation_result

TOLERABLE_ANGLE_PER_SECOND = [0.001, 0.001025, 0.00105, 0.001075, 0.0011, 0.001125, 0.00115, 0.001175, 0.0012, 0.001225, 0.00125]
# TOLERABLE_ANGLE_PER_SECOND = [0.1]
# ALGORITHMS = ["DTDR", "DDR", "OPSPF", "DTDRwG", "DDRwG", "OPSPFwG"]
ALGORITHMS = ["OPSPF"]

def run_main_py(args):
    angle, algorithm = args
    # print(algorithm)
    process = subprocess.Popen(['python', 'main.py', str(angle), algorithm])
    process.wait()  # main.py가 종료될 때까지 기다림
    time.sleep(2)  # 재시작 전 약간의 지연 시간 (필요에 따라 조정)

def run_main_py_with_args(algorithm):
    args = [(angle, algorithm) for angle in TOLERABLE_ANGLE_PER_SECOND]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(run_main_py, args)

if __name__ == "__main__":
    # set_routing_simulation_result("OPSPFwG")
    # print("OPSPFwG")
    # run_main_py_with_args("OPSPFwG")
    for algorithm in ALGORITHMS:
        set_routing_simulation_result(algorithm)
        print(algorithm)
        run_main_py_with_args(algorithm)

