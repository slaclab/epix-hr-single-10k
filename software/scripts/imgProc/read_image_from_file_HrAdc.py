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
import ePixViewer.Cameras as cameras
import ePixViewer.imgProcessing as imgPr
# 
import matplotlib   
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import h5py

#matplotlib.pyplot.ion()
NUMBER_OF_PACKETS_PER_FRAME = 2
#MAX_NUMBER_OF_FRAMES_PER_BATCH  = 1500*NUMBER_OF_PACKETS_PER_FRAME
MAX_NUMBER_OF_FRAMES_PER_BATCH  = -1

PAYLOAD_SERIAL_FRAME = 4112 #2064
PAYLOAD_TS           = 7360

##################################################
# Global variables
##################################################
cameraType            = 'ePixHrePixM'
bitMask               = 0xffff
GET_SERIAL_OR_TS_DATA = True # True serial data, false TS data
PLOT_IMAGE            = True
PLOT_IMAGE_DARKSUB    = False
PLOT_IMAGE_DARK       = False
PLOT_IMAGE_HEATMAP    = False
PLOT_SET_HISTOGRAM    = False
PLOT_ADC_VS_N         = False
SAVEHDF5              = True

##################################################
# Dark images
##################################################
if (len(sys.argv[1])>0):
    filename = sys.argv[1]
else:
    filename = ''

f = open(filename, mode = 'rb')

file_header = [0]
numberOfFrames = 0
while ((len(file_header)>0) and ((numberOfFrames<MAX_NUMBER_OF_FRAMES_PER_BATCH) or (MAX_NUMBER_OF_FRAMES_PER_BATCH==-1))):
    try:
        # reads file header [the number of bytes to read, EVIO]
        file_header = np.fromfile(f, dtype='uint32', count=2)
        payloadSize = int(file_header[0]/4)-1 #-1 is need because size info includes the second word from the header
        if ((GET_SERIAL_OR_TS_DATA == True) and (file_header[0] != PAYLOAD_SERIAL_FRAME)):
            print ('size',  file_header)
            pause(1)

        #save only serial data frames
        if ((GET_SERIAL_OR_TS_DATA == True) and (file_header[0] == PAYLOAD_SERIAL_FRAME)):
            newPayload = np.fromfile(f, dtype='uint32', count=payloadSize) #(frame size splited by four to read 32 bit 
            if (numberOfFrames == 0):
                allFrames = [newPayload.copy()]
            else:
                newFrame  = [newPayload.copy()]
                allFrames = np.append(allFrames, newFrame, axis = 0)
            numberOfFrames = numberOfFrames + 1 
            #print ("Payload" , numberOfFrames, ":",  (newPayload[0:5]))
            previousSize = file_header
        #save only TS data frames
        if ((GET_SERIAL_OR_TS_DATA == False) and (file_header[0] == PAYLOAD_TS)):
            newPayload = np.fromfile(f, dtype='uint32', count=payloadSize) #(frame size splited by four to read 32 bit 
            if (numberOfFrames == 0):
                allFrames = [newPayload.copy()]
            else:
                newFrame  = [newPayload.copy()]
                allFrames = np.append(allFrames, newFrame, axis = 0)
            numberOfFrames = numberOfFrames + 1 
            #print ("Payload" , numberOfFrames, ":",  (newPayload[0:5]))
            previousSize = file_header
        if (numberOfFrames%1000==0):
            print("Read %d frames" % numberOfFrames)

    except Exception: 
        e = sys.exc_info()[0]
        print ("Message\n", e)
        print ('size', file_header, 'previous size', previousSize)
        print("numberOfFrames read: " ,numberOfFrames)


##################################################
# image descrambling
##################################################
currentCam = cameras.Camera(cameraType = cameraType)
currentCam.bitMask = bitMask
#numberOfFrames = allFrames.shape[0]
print("numberOfFrames in the 3D array: " ,numberOfFrames)
print("Starting descrambling images")
currentRawData = []
imgDesc = []
if(numberOfFrames==1):
    [frameComplete, readyForDisplay, rawImgFrame] = currentCam.buildImageFrame(currentRawData = [], newRawData = allFrames[0])
    imgDesc = np.array([currentCam.descrambleImage(bytearray(rawImgFrame.tobytes()))])
else:
    for i in range(0, numberOfFrames):
        #get an specific frame
        [frameComplete, readyForDisplay, rawImgFrame] = currentCam.buildImageFrame(currentRawData, newRawData = allFrames[i,:])
        currentRawData = rawImgFrame

        #get descrambled image from camera
        if (len(imgDesc)==0 and (readyForDisplay)):
            imgDesc = np.array([currentCam.descrambleImage(rawImgFrame)],dtype=np.float)
            currentRawData = []
        else:
            if readyForDisplay:
                currentRawData = []
                newImage = currentCam.descrambleImage(rawImgFrame)
                newImage = newImage.astype(np.float, copy=False)
                #if (np.sum(np.sum(newImage))==0):
                #    newImage[np.where(newImage==0)]=np.nan
                imgDesc = np.concatenate((imgDesc, np.array([newImage])),0)
if(SAVEHDF5):
    print("Saving Hdf5")
    h5_filename = os.path.splitext(filename)[0]+".hdf5"
    f = h5py.File(h5_filename, "w")
    f['hrAdc'] = imgDesc.astype('uint16')
    f.close()

##################################################
#from here on we have a set of images to work with
##################################################
#show first image
if PLOT_IMAGE :
    for i in range(0, 1):
        plt.imshow(imgDesc[i,:,:], interpolation='nearest')
        plt.gray()
        plt.colorbar()
        plt.title('First image of :'+filename)
        plt.show()
    plt.plot(imgDesc[:,15,15])
    plt.plot(imgDesc[:,15,45])
    plt.title('Pixel time series (15,15) and (15,45) :'+filename)
    plt.show()

darkImg = np.mean(imgDesc, axis=0)
print(darkImg.shape)


if PLOT_IMAGE_DARK :
    plt.imshow(darkImg, interpolation='nearest')
    plt.gray()
    plt.colorbar()
    plt.title('Dark image map of :'+filename)
    plt.show()

heatMap = np.std(imgDesc, axis=0)
if PLOT_IMAGE_HEATMAP :
    plt.imshow(heatMap, interpolation='nearest', vmin=0, vmax=200)
    plt.gray()
    plt.colorbar()
    plt.title('Heat map of :'+filename)
    plt.show()

darkSub = imgDesc - darkImg
if PLOT_IMAGE_DARKSUB :
    for i in range(0, 1):
        #plt.imshow(darkSub[i,:,0:31], interpolation='nearest')
        plt.imshow(darkSub[i,:,:], interpolation='nearest')
        plt.gray()
        plt.colorbar()
        plt.title('First image of :'+filename)
        plt.show()



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


standAloneADCPlot = 45
centralValue_even = np.average(imgDesc[0,np.arange(0,32,2),standAloneADCPlot])
centralValue_odd  = np.average(imgDesc[0,np.arange(1,32,2),standAloneADCPlot])
# the histogram of the data
if PLOT_SET_HISTOGRAM :
    nbins = 100
    EnergyTh = -50
    n_even = np.zeros(nbins)
    n_odd  = np.zeros(nbins)
    for i in range(0, imgDesc.shape[0]):
    #    n, bins, patches = plt.hist(darkSub[5,:,:], bins=256, range=(0.0, 256.0), fc='k', ec='k')
    #    [x,y] = np.where(darkSub[i,:,32:63]>EnergyTh)
    #   h, b = np.histogram(darkSub[i,x,y], np.arange(-nbins/2,nbins/2+1))
    #    h, b = np.histogram(np.average(darkSub[i,:,5]), np.arange(-nbins/2,nbins/2+1))
        h, b = np.histogram(np.average(imgDesc[i,np.arange(0,32,2),standAloneADCPlot]), np.arange(centralValue_even-nbins/2,centralValue_even+nbins/2+1))
        n_even = n_even + h
        h, b = np.histogram(np.average(imgDesc[i,np.arange(1,32,2),standAloneADCPlot]), np.arange(centralValue_odd-nbins/2,centralValue_odd+nbins/2+1))
        n_odd = n_odd + h

    np.savez("adc_" + str(standAloneADCPlot), imgDesc[:,:,standAloneADCPlot])

    plt.bar(b[1:nbins+1],n_even, width = 0.55)
    plt.bar(b[1:nbins+1],n_odd,  width = 0.55,color='red')
    plt.title('Histogram')
    plt.show()


numColumns = 64
averages = np.zeros([imgDesc.shape[0],numColumns])
noises   = np.zeros([imgDesc.shape[0],numColumns])
if PLOT_ADC_VS_N :
    for i in range(0, imgDesc.shape[0]):
        averages[i] = np.mean(imgDesc[i], axis=0)
        noises[i]   = np.std(imgDesc[i], axis=0)

    #rolls matrix to enable dnl[n] = averages[n+1] - averages[n]
    dnls = np.roll(averages,-1, axis=0) - averages

    # All averages
    plt.plot(averages)
    plt.title('Average ADC value')
    plt.show()
    # All stds
    plt.plot(noises)
    plt.title('Standard deviation of the ADC value')
    plt.show()
    #dnl
    plt.plot(dnls)
    plt.title('DNL of the ADC value')
    plt.show()

    # All averages and stds
    plt.figure(1)
    plt.subplot(211)
    plt.title('Average ADC value')
    plt.plot(averages)

    plt.subplot(212)
    plt.plot(noises)
    plt.title('Standard deviation of the ADC value')
    plt.show()

    # selected ADC
    plt.figure(1)
    plt.subplot(211)
    plt.title('Average ADC value')
    customLabel = "ADC_"+str(standAloneADCPlot)
    line, = plt.plot(averages[:,standAloneADCPlot], label=customLabel)
    plt.legend(handles = [line])

    plt.subplot(212)
    plt.plot(noises[:, standAloneADCPlot], label="ADC_"+str(standAloneADCPlot))
    plt.title('Standard deviation of the ADC value')
    plt.show()

print (np.max(averages,axis=0) -  np.min(averages,axis=0))




    


