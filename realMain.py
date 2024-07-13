import subprocess
import time
import concurrent.futures

from util import set_routing_simulation_result

TOLERABLE_ANGLE_PER_SECOND = [0.001, 0.001025, 0.00105, 0.001075, 0.0011, 0.001125, 0.00115, 0.001175, 0.0012, 0.001225, 0.00125]

def run_main_py(angle):
    process = subprocess.Popen(['python', 'main.py', str(angle)])
    process.wait()  # main.py가 종료될 때까지 기다림
    time.sleep(2)  # 재시작 전 약간의 지연 시간 (필요에 따라 조정)

def run_main_py_with_args():
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
        executor.map(run_main_py, TOLERABLE_ANGLE_PER_SECOND)

if __name__ == "__main__":
    set_routing_simulation_result()
    run_main_py_with_args()
