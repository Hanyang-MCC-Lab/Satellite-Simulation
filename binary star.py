from vpython import *
#Web VPython 3.2

G = 6.7e-11 # Newton gravitational constant

giant = sphere(pos=vector(-1e11,0,0), radius=2e10, color=color.red)
giant.mass = 2e30
giant.p = vector(0, 0, -1e4) * giant.mass

dwarf = sphere(pos=vector(1e11,0,0), radius=1e10, color=color.yellow,
                make_trail=True, interval=5, retain=10)
dwarf.mass = 1e30
dwarf.p = -giant.p

dt = 1e5
while True:
    rate(10)
    r = dwarf.pos - giant.pos
    F = G * giant.mass * dwarf.mass * r.hat / mag(r)**2
    dwarf.p = dwarf.p - F*dt
    dwarf.pos = dwarf.pos + (dwarf.p/dwarf.mass) * dt