'Python 3.7'
from vpython import *
from tkinter import *

root = Tk()

monitor_height = root.winfo_screenheight()
monitor_width = root.winfo_screenwidth()

scene = canvas(width = monitor_width-15, height = monitor_height-15)
scene.resizable = False
box()
earth = sphere(pos=vec(0, 0, 0), radius=10, texture=textures.earth)
orbit = ring(pos=vector(0, 0, 0), axis=vector(0, 1, 0), radius=12, color=color.red, thickness=0.1)