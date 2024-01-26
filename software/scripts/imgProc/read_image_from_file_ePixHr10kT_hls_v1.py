#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 10 10:52:45 2023

@author: ddoering
"""
import os, sys, time
import numpy as np
#import ePixViewer.Cameras as cameras
#import ePixViewer.imgProcessing as imgPr
# 
import matplotlib   
#matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import h5py
import scipy.ndimage
import matplotlib.patches 
import rogue.protocols

#%%

filename = '/u2/ddoering/test_epixHR_hls_cores_dark.dat'
localfile = open(filename, mode = 'rb')
file_header = np.fromfile(localfile, dtype='uint32', count=2)
payloadSize = int(file_header[0]/2)-2 #-1 is need because size info includes the second word from the header
newPayload = np.fromfile(localfile, dtype='uint16', count=payloadSize) #(frame size splited by four to read 32 bit 

unbatcher = rogue.protocols.batcher.SplitterV1()

image = np.array(newPayload[0:-16])
image2 = image.reshape(146,-1)
for i in range(100):
    payloadSize = int(file_header[0]/2)-2 #-1 is need because size info includes the second word from the header
    newPayload = np.fromfile(localfile, dtype='uint16', count=payloadSize) #(frame size splited by four to read 32 bit 
    image = np.array(newPayload[0:-16])
    image2 = image.reshape(146,-1)
    
plt.imshow(image2)

localfile.close()


#%%
fluxes = np.load("/u1/ddoering/mfxx1005021_252_c0_fluxes.npy")
#%%
plt.plot(fluxes)

#%%
frames = np.load("/u1/ddoering/mfxx1005021_252_c0_frames.npy")
#%%
plt.imshow(frames[0])
