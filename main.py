'Python 3.7'
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
inclination = float(input("Please input Orbit Inclination radian.\n Orbit Inclination : ")) #궤도경사

#씬 구성
#기준 춘분점(Reference direction vector = (1, 0, 0))
scene = canvas(width = monitor_width-15, height = monitor_height-15)
scene.resizable = False

# xy평면과 x, y, z축
mybox = box(pos=vec(0, 0, 0), length=30000, height=1, width=30000, opacity=0.5)
lineX = arrow(pos=vector(-15000, 0, 0), axis=vector(1, 0, 0), shaftwidth=50, headwidth=300, headlength=300, length=30000, color=color.magenta)
lineY = arrow(pos=vector(0, 0, -15000), axis=vector(0, 0, 1), shaftwidth=50, headwidth=300, headlength=300, length=30000, color=color.blue)
lineZ = arrow(pos=vector(0, -10000, 0), axis=vector(0, 1, 0), shaftwidth=50, headwidth=300, headlength=300, length=20000, color=color.green)

# 궤도처리
orbit = []
sat = []

earth = sphere(pos=vec(0, 0, 0), radius=CONST_EARTH_RADIUS, texture=textures.earth) #지구생성

for i in range(CONST_ORBIT_NUM): #궤도생성
    orbit[i] = ring(pos=vec(1, 0, 0), axis=vec(0, math.cos(inclination), math.sin(inclination)), radius=CONST_SAT_RADIUS, color=color.red, thickness=15)
    for j in range(CONST_SAT_NUM): #위성생성
        sat[j] = sphere(pos=vec(CONST_SAT_RADIUS, 0, 0), axis=vec(0, math.cos(inclination), math.sin(inclination)), radius=30, color=color.white)