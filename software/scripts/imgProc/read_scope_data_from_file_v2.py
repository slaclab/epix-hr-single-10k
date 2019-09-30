#-----------------------------------------------------------------------------
# Title      : read images from file script
#-----------------------------------------------------------------------------
# File       : read_image_from_file.py
# Created    : 2017-06-19
# Last update: 2017-06-21
#-----------------------------------------------------------------------------
# Description:
# Simple image viewer that enble a local feedback from data collected using
# ePix cameras. The initial intent is to use it with stand alone systems
#
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import os, sys, time
import numpy as np
#import ePixViewer.Cameras as cameras
#import ePixViewer.imgProcessing as imgPr
# 
import matplotlib   
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import h5py

#matplotlib.pyplot.ion()
NUMBER_OF_PACKETS_PER_FRAME = 1
#MAX_NUMBER_OF_FRAMES_PER_BATCH  = 1500*NUMBER_OF_PACKETS_PER_FRAME
MAX_NUMBER_OF_FRAMES_PER_BATCH  = -1


##################################################
# Global variables
##################################################
PLOT_SET_HISTOGRAM    = False
PLOT_ADC_VS_N         = True

##################################################
# Dark images
##################################################
#if (len(sys.argv[1])>0):
#    filename = sys.argv[1]
#else:
#filename = '/data/cryoData/backend/pulse_pseudoScope.dat'
filename = '/data/cryoData/coldMeasurements/singleChRamp.dat'
filename = '/data/cryoData/frontend/atest_pulser_test_analogMonitor_and_image.dat'
filename = '/data/cryoData/EXO_Lab/Full_Chain/Pulser_Linearity/Pulser_lin_Ch_0_8_3f_37_0x13ad_t3p6u_g3x0.dat'
f = open(filename, mode = 'rb')

file_header = [0]
numberOfFrames = 0
previousSize = 0
while ((len(file_header)>0) and ((numberOfFrames<MAX_NUMBER_OF_FRAMES_PER_BATCH) or (MAX_NUMBER_OF_FRAMES_PER_BATCH==-1))):
    try:
        # reads file header [the number of bytes to read, EVIO]
        file_header = np.fromfile(f, dtype='uint32', count=2)
        payloadSize = int(file_header[0]/4)-1 #-1 is need because size info includes the second word from the header
        print ('packet size',  file_header)
        

        #save only serial data frames
        newPayload = np.fromfile(f, dtype='uint16', count=payloadSize*2) #(frame size splited by four to read 32 bit 
        if ((file_header[1]&0xff000000)>>24)==2: #image packet only, 2 mean scope data
            if (numberOfFrames == 0):
                allFrames = [newPayload.copy()]
            else:
                newFrame  = [newPayload.copy()]
                allFrames = np.append(allFrames, newFrame, axis = 0)
            numberOfFrames = numberOfFrames + 1 
            previousSize = file_header
        
        if (numberOfFrames%5000==0):
            print("Read %d frames" % numberOfFrames)

    except Exception: 
        e = sys.exc_info()[0]
        #print ("Message\n", e)
        print("End of file.")
        print ('size', file_header, 'previous size', previousSize)
        print("numberOfFrames read: " ,numberOfFrames)



##################################################
#from here on we have a set of traces to work with
##################################################
np.savetxt(os.path.splitext(filename)[0] + "_traces" + ".csv", allFrames, fmt='%d', delimiter=',', newline='\n')

#%%
if PLOT_ADC_VS_N :
    
    # All single and all traces
    plt.figure(1)
    plt.subplot(211)
    plt.title('ADC value - single trace')
    plt.plot(allFrames[1,20:-20])

    plt.subplot(212)
    plt.plot(np.transpose(allFrames[:, 20:-20]))
    plt.title('ADC value - all traces')
    plt.show()

    

#%%
testSignal = allFrames[1]
print(testSignal[20:30])
vhex = np.vectorize(hex)
print(vhex(testSignal[20:30]))
LSBArray = np.bitwise_and(testSignal,255)
MSBArray = np.bitwise_and(testSignal,65280)
#print(vhex(LSBArray[20:30]))
#print(vhex(MSBArray[20:30]))
newSignal = MSBArray[0:-1] + LSBArray[1:]
newSignal2 = MSBArray[1:] + LSBArray[0:-1]
difSignal = testSignal[:-1] - newSignal
print(vhex(newSignal[20:30]))

if PLOT_ADC_VS_N :
    plt.figure(2)
    plt.subplot(311)
    plt.title('ADC value - single trace')
    plt.plot(testSignal[20:-20])

    plt.subplot(312)
    plt.plot(np.transpose(newSignal[20:-20]))
    plt.title('ADC value - all traces')

    plt.subplot(313)
    plt.plot(np.transpose(newSignal2[20:-20]))
    plt.title('ADC value - all traces')
   
    plt.show()
#%%
allFramesInVolts = allFrames[:,20:-20]*(-2.5/16384)+2.5
if PLOT_ADC_VS_N :
    
    # All single and all traces
    plt.figure(1)
    plt.subplot(211)
    plt.title('ADC value - single trace')
    plt.plot(allFramesInVolts[1])

    plt.subplot(212)
    plt.plot(np.transpose(allFramesInVolts))
    plt.title('ADC value - all traces')
    plt.show()
    
#%%
maxValues = np.max(allFramesInVolts,1)
if PLOT_ADC_VS_N :
    
    # All single and all traces
    plt.figure(1)
    plt.subplot(211)
    plt.title('ADC value - single trace')
    plt.plot(maxValues[0:666])

    plt.subplot(212)
    plt.plot(np.transpose(allFramesInVolts[112,0:1023]))
    plt.plot(np.transpose(allFramesInVolts[300,0:1023]))
    plt.plot(np.transpose(allFramesInVolts[484,0:1023]))
    plt.title('ADC value - all traces')
    plt.show()
    
    
#%%
# the histogram of the data
centralValue = 0
if PLOT_SET_HISTOGRAM :
    nbins = 100
    EnergyTh = -50
    n = np.zeros(nbins)
    for i in range(0, imgDesc.shape[0]):
    #    n, bins, patches = plt.hist(darkSub[5,:,:], bins=256, range=(0.0, 256.0), fc='k', ec='k')
    #    [x,y] = np.where(darkSub[i,:,32:63]>EnergyTh)
    #   h, b = np.histogram(darkSub[i,x,y], np.arange(-nbins/2,nbins/2+1))
    #    h, b = np.histogram(np.average(darkSub[i,:,5]), np.arange(-nbins/2,nbins/2+1))
        dataSet = darkSub[i,:,5]
        h, b = np.histogram(np.average(dataSet), np.arange(centralValue-nbins/2,centralValue+nbins/2+1))
        n = n + h

    plt.bar(b[1:nbins+1],n, width = 0.55)
    plt.title('Histogram')
    plt.show()









    


