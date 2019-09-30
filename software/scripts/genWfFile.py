import numpy as np

t = np.zeros(1024, dtype=int)

#generates a ramp
for i in range (0,1024):
    t[i]=i

np.savetxt("ramp_9000h_b.csv", (t%128)*32+36864, fmt='%d')

#generates a sin
s = np.sin(t*2*3.14159265/64)*(32767/3)+(24576)

np.savetxt("sin128.csv", s, fmt='%d')

