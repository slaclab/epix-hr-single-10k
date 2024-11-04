#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 24 12:00:44 2023

@author: ddoering
"""
import numpy as np

NROWS = 145
NCOLS_PER_STREM = 32
NSTREAMS = 12
#%%
#build data
data_corrected =  np.zeros((NROWS,(NCOLS_PER_STREM*NSTREAMS)), np.uint16)
for row in range (NROWS):
    for col in range (NCOLS_PER_STREM*NSTREAMS):
        data_corrected[row, col] = row+col
#%%        
#build dark
dark_image  =  np.ones((NROWS,(NCOLS_PER_STREM*NSTREAMS)), np.uint16)*3000

#%%
#build gains
gainErrors =  np.zeros((NROWS,(NCOLS_PER_STREM*NSTREAMS)), np.uint16)
for row in range (NROWS):
    for col in range (NCOLS_PER_STREM*NSTREAMS):
        gainErrors[row, col] = (row%2)+1

#gain correction scaled to 7 bits as unit gain
gains  = np.uint16(1/(gainErrors)*128)

raw_image = (data_corrected*gainErrors+dark_image)

#%%
#check that all works
recoverd_image = (raw_image-dark_image)
#%%
recoverd_image = (recoverd_image.astype(np.uint32)*gains.astype(np.uint32))
#%%
recoverd_image = (recoverd_image/128).astype(np.uint16)
#%%
total_error = np.sum(np.sum(data_corrected-recoverd_image))
if (total_error):
    print("test failed")
else:
    print("success")
#%%
fp = open("raw145by384.csv", "bw")
raw_image.tofile(fp,", ")
fp.close()
#%%
fp = open("gains145by384.csv", "bw")
gains.tofile(fp,", ")
fp.close()

fp = open("dark145by384.csv", "bw")
dark_image.tofile(fp,", ")
fp.close()

fp = open("galdenImage145by384.csv", "bw")
data_corrected.tofile(fp,", ")
fp.close()

#%%
readback = np.fromfile("dark145by384.csv",sep=", ",  dtype=np.uint16)
#%%
