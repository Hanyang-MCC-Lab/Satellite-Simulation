'Python 3.7'
'Web VPython 3.2'
import orbit as orbit
from vpython import *
from tkinter import *
import math

#상수선언
CONST_EARTH_RADIUS = 6371 #지구반경
CONST_SAT_RADIUS = CONST_EARTH_RADIUS + 550 #지구반경 + 550KM
CONST_ORBIT_NUM = 72 #궤도개수
CONST_SAT_NUM = 22 #위성개수

#모니터 해상도에 따라 유동적인 해상도 조절
root = Tk()
monitor_height = root.winfo_screenheight()
monitor_width = root.winfo_screenwidth()

#케플러 요소 입력
inclination = math.radians(float(input("Please input Orbit Inclination radian.\n Orbit Inclination : "))) #궤도경사

#씬 구성
#기준 춘분점(Reference direction vector = (1, 0, 0))
scene = canvas(width = monitor_width-15, height = monitor_height-15)
scene.resizable = False
box()
#궤도 및 위성 리스트 생성
orbit = []
sat = []

earth = sphere(pos=vec(1, 0, 0), radius=CONST_EARTH_RADIUS, texture=textures.earth) #지구생성

orbit1 = ring(pos=vec(0, 0, 0), axis=vec(math.cos(math.sin(0))-math.sin(math.sin(inclination)), math.cos(inclination), math.sin(math.sin(0))+math.cos(math.sin(inclination))), radius=CONST_SAT_RADIUS, color=color.red, thickness=15)
orbit2 = ring(pos=vec(0, 0, 0), axis=vec(0, math.cos(inclination), math.sin(inclination)), radius=CONST_SAT_RADIUS, color=color.cyan, thickness=15)
#orbit3 = ring(pos=vec(0, 0, 0), axis=vec(math.sin(0.16), math.cos(inclination), math.sin(inclination)+math.sin(0.16)), radius=CONST_SAT_RADIUS, color=color.white, thickness=15)
    #for j in range(CONST_SAT_NUM): #위성생성
        #sat[j] = sphere(pos=vec(CONST_SAT_RADIUS, 0, 0), axis=vec(0, math.cos(inclination / 180), math.sin(inclination / 180)), radius=30, color=color.white)
