#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : local image viewer for the ePix camera images
#-----------------------------------------------------------------------------
# File       : ePixViewer.py
# Author     : Dionisio Doering
# Created    : 2017-02-08
# Last update: 2017-02-08
#-----------------------------------------------------------------------------
# Description:
# Describes the camera main parameters and implements descrambling function
# 
#
#-----------------------------------------------------------------------------
# This file is part of the ATLAS CHESS2 DEV. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ATLAS CHESS2 DEV, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import sys
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue    
import time
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import QObject, pyqtSignal
import numpy as np
import ePixViewer.imgProcessing as imgPr

PRINT_VERBOSE = 0

# define global constants
NOCAMERA   = 0
EPIX100A   = 1
EPIX100P   = 2
TIXEL48X48 = 3
EPIX10KA   = 4

################################################################################
################################################################################
#   Camera class
#   Define camera specific parameters and descrambler functions
#   After using this class the image of all cameras should be a 2d matrix
#   with sensor heigh, width with a given pixel depth
################################################################################
class Camera():
    """implements basic image processing specific to the SLAC cameras"""

    # define global properties
    cameraType = ""
    cameraModule = ""
    sensorWidth = 0
    sensorHeight = 0
    pixelDepth = 0
    availableCameras = {  'ePix100a':  EPIX100A, 'ePix100p' : EPIX100P, 'Tixel48x48' : TIXEL48X48, 'ePix10ka' : EPIX10KA }
    

    def __init__(self, cameraType = 'ePix100a') :
        
        camID = self.availableCameras.get(cameraType, NOCAMERA)

        # check if the camera exists
        print("Camera ", cameraType, " selected.")
        if (camID == NOCAMERA):
            print("Camera ", cameraType ," not supported")
            
        self.cameraType = cameraType

        #selcts proper initialization based on camera type
        if (camID == EPIX100A):
            self._initEPix100a()
        if (camID == EPIX100P):
            self._initEPix100p()
        if (camID == TIXEL48X48):
            self._initTixel48x48()
        if (camID == EPIX10KA):
            self._initEpix10ka()

        #creates a image processing tool for local use
        self.imgTool = imgPr.ImageProcessing(self)
        
    # return a dict with all available cameras    
    def getAvailableCameras():
        return self.availableCameras

    # return the descrambled image based on the current camera settings
    def descrambleImage(self, rawData):
        camID = self.availableCameras.get(self.cameraType, NOCAMERA)
        if (camID == EPIX100A):
            descImg = self._descrambleEPix100aImage(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == EPIX100P):
            descImg = self._descrambleEPix100aImage(rawData)        
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == TIXEL48X48):
            descImg = self._descrambleTixel48x48Image(rawData) 
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == EPIX10KA):
            descImg = self._descrambleEPix100aImage(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == NOCAMERA):
            return Null

    # return
    def buildImageFrame(self, currentRawData, newRawData):
        camID = self.availableCameras.get(self.cameraType, NOCAMERA)

        ##if (PRINT_VERBOSE): print('buildImageFrame - camID: ', camID)

        frameComplete = 0
        readyForDisplay = 0
        if (camID == EPIX100A):
            # The flags are always true since each frame holds an entire image
            frameComplete = 1
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == EPIX100P):
            # The flags are always true since each frame holds an entire image
            frameComplete = 1
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == TIXEL48X48):
            #Needs to check the two frames and make a decision on the flags
            [frameComplete, readyForDisplay, newRawData]  = self._buildFrameTixel48x48Image(currentRawData, newRawData)
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == EPIX10KA):
            # The flags are always true since each frame holds an entire image
            frameComplete = 1
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == NOCAMERA):
            return Null

    ##########################################################
    # define all camera specific init values
    ##########################################################
    def _initEPix100a(self):
        self._superRowSize = 384
        self._NumAsicsPerSide = 2
        self._NumAdcChPerAsic = 4
        self._NumColPerAdcCh = 96
        self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth = self._calcImgWidth()
        self.sensorHeight = 708
        self.pixelDepth = 16
        self.cameraModule = "Standard ePix100a"
        self.bitMask = np.uint16(0xFFFF)

    def _initEPix100p(self):
        self._superRowSize = 384
        self._NumAsicsPerSide = 2
        self._NumAdcChPerAsic = 4
        self._NumColPerAdcCh = 96
        self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth = self._calcImgWidth()
        self.sensorHeight = 706
        self.pixelDepth = 16
        self.bitMask = np.uint16(0xFFFF)

    def _initTixel48x48(self):
        #self._superRowSize = 384
        self._NumAsicsPerSide = 1
        #self._NumAdcChPerAsic = 4
        #self._NumColPerAdcCh = 96
        #self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth  = 96 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.sensorHeight = 96 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.pixelDepth = 16
        self.bitMask = np.uint16(0xFFFF)

    def _initEpix10ka(self):
        self._superRowSize = int(384/2)
        self._NumAsicsPerSide = 2
        self._NumAdcChPerAsic = 4
        self._NumColPerAdcCh = int(96/2)
        self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth = self._calcImgWidth()
        self.sensorHeight = 356#706
        self.pixelDepth = 16
        self.cameraModule = "Standard ePix10ka"
        self.bitMask = np.uint16(0x3FFF)

    ##########################################################
    # define all camera specific build frame functions
    ##########################################################
    def _buildFrameTixel48x48Image(self, currentRawData, newRawData):
        """ Performs the Tixel frame building.
            For this sensor the image takes four frames, twa with time of arrival info
            and two with time over threshold. There is no guarantee both frames will always arrive nor on their order."""
        #init local variables
        frameComplete = 0
        readyForDisplay = 0
        returnedRawData = []
        acqNum_currentRawData  = 0
        isTOA_currentRawData   = 0
        asicNum_currentRawData = 0
        acqNum_newRawData  = 0
        isTOA_newRawData   = 0
        asicNum_newRawData = 0

        
        ##if (PRINT_VERBOSE): print('\nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        ##if (PRINT_VERBOSE): print('\nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        isTOA_newRawData   = (newRawData_DW[2] & 0x8) >> 3        # header dword 2  
        asicNum_newRawData =  newRawData_DW[2] & 0x7              # header dword 2
        ##if (PRINT_VERBOSE): print('\nacqNum_newRawData: ', acqNum_newRawData, '\nisTOA_newRawData:', isTOA_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)


        #interpret headers
        #case 1: new image (which means currentRawData is empty)
        if (len(currentRawData) == 0):
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((1156,),dtype='uint32')# 2310 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z,z,z])
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            isTOA_currentRawData   = isTOA_newRawData
            asicNum_currentRawData = asicNum_newRawData
        #case where the currentRawData is a byte array
        elif(len(currentRawData) == 4620):
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((1156,),dtype='uint32')# 2310 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z,z,z])
            #
            currentRawData_DW = np.frombuffer(currentRawData,dtype='uint32')
                                                                             # header dword 0 (VC info)
            acqNum_currentRawData  =  currentRawData_DW[1]                   # header dword 1
            isTOA_currentRawData   = (currentRawData_DW[2] & 0x8) >> 3       # header dword 2  
            asicNum_currentRawData =  currentRawData_DW[2] & 0x7             # header dword 2

            currentRawData = self.fill_memory(returnedRawData, asicNum_currentRawData, isTOA_currentRawData, currentRawData_DW)
            returnedRawData = currentRawData
        
        elif(len(currentRawData)==4):
            #recovers currentRawData header info
            #loop traverses the four traces to find the info
            for j in range(0,4):
                #print(len(currentRawData))
                if(currentRawData[j,0]==1):
                                                                                # extended header dword 0 (valid trace)
                                                                                # extended header dword 1 (VC info)
                    acqNum_currentRawData  =  currentRawData[j,2]               # extended header dword 2 (acq num)
                    isTOA_currentRawData   = (currentRawData[j,3] & 0x8) >> 3   # extended header dword 3 
                    asicNum_currentRawData =  currentRawData[j,3] & 0x7         # extended header dword 1 (VC info)
            #saves current data on returned data before adding new data
            returnedRawData = currentRawData
        else:
            #packet size error
            if (PRINT_VERBOSE): print('\n packet size error, packet len: ', len(currentRawData))

        ##if (PRINT_VERBOSE): print('\nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        ##if (PRINT_VERBOSE): print('\nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]

        #fill the memory with the new data (when acqNums matches)
        returnedRawData = self.fill_memory(returnedRawData, asicNum_newRawData, isTOA_newRawData, newRawData_DW)
        ##if (PRINT_VERBOSE): print('Return data 0:', returnedRawData[0,0:10])
        ##if (PRINT_VERBOSE): print('Return data 1:', returnedRawData[1,0:10])
        ##if (PRINT_VERBOSE): print('Return data 2:', returnedRawData[2,0:10])
        ##if (PRINT_VERBOSE): print('Return data 3:', returnedRawData[3,0:10])

        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        ##if (PRINT_VERBOSE): print('\nisValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        ##if (PRINT_VERBOSE): print('\nisValidTrace1', isValidTrace1)
        isValidTrace2 =  returnedRawData[2,0]
        ##if (PRINT_VERBOSE): print('\nisValidTrace2', isValidTrace2)
        isValidTrace3 =  returnedRawData[3,0]
        ##if (PRINT_VERBOSE): print('\nisValidTrace3', isValidTrace3)

        if((isValidTrace0 == 1) and (isValidTrace1 == 1) and (isValidTrace2 == 1) and (isValidTrace3 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0

        ##if (PRINT_VERBOSE): print('frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]

    #fill the memory with the new data (when acqNums matches)
    def fill_memory(self, returnedRawData, asicNum_currentRawData, isTOA_currentRawData, newRawData_DW):
        ##if (PRINT_VERBOSE): print('New data:', newRawData_DW[0:10])
        if (len(newRawData_DW)==1155):
            if(asicNum_currentRawData==0 and isTOA_currentRawData==0):
                returnedRawData[0,0]  = 1
                returnedRawData[0,1:] = newRawData_DW
            if(asicNum_currentRawData==1 and isTOA_currentRawData==0):
                returnedRawData[1,0]  = 1
                returnedRawData[1,1:] = newRawData_DW
            if(asicNum_currentRawData==0 and isTOA_currentRawData==1):
                returnedRawData[2,0]  = 1
                returnedRawData[2,1:] = newRawData_DW
            if(asicNum_currentRawData==1 and isTOA_currentRawData==1):
                returnedRawData[3,0]  = 1
                returnedRawData[3,1:] = newRawData_DW
            ##if (PRINT_VERBOSE): print('Return data 0:', returnedRawData[0,0:10])
            ##if (PRINT_VERBOSE): print('Return data 1:', returnedRawData[1,0:10])
            ##if (PRINT_VERBOSE): print('Return data 2:', returnedRawData[2,0:10])
            ##if (PRINT_VERBOSE): print('Return data 3:', returnedRawData[3,0:10])
        return returnedRawData


    ##########################################################
    # define all camera specific descrabler functions
    ##########################################################

    def _descrambleEPix100pImage(self, rawData):
        """performs the ePix100p image descrambling"""
        
        #removes header before displying the image
        for j in range(0,32):
            rawData.pop(0)
        
        #get the first superline
        imgBot = rawData[(0*self._superRowSizeInBytes):(1*self._superRowSizeInBytes)] 
        imgTop = rawData[(1*self._superRowSizeInBytes):(2*self._superRowSizeInBytes)] 
        for j in range(2,self.sensorHeight):
            if (j%2):
                imgBot.extend(rawData[(j*self._superRowSizeInBytes):((j+1)*self._superRowSizeInBytes)])
            else:
                imgTop.extend(rawData[(j*self._superRowSizeInBytes):((j+1)*self._superRowSizeInBytes)]) 
        imgDesc = imgBot
        imgDesc.extend(imgTop)

        # convert to numpy array
        imgDesc = np.array(imgDesc,dtype='uint8')

        # returns final image
        return imgDesc


    def _descrambleEPix100aImageAsByteArray(self, rawData):
        """performs the ePix100a image descrambling (this is a place holder only)"""
        
        #removes header before displying the image
        for j in range(0,32):
            rawData.pop(0)
        
        #get the first superline
        imgBot = bytearray()
        imgTop = bytearray()
        for j in range(0,self.sensorHeight):
            if (j%2):
                imgTop.extend(rawData[((self.sensorHeight-j)*self._superRowSizeInBytes):((self.sensorHeight-j+1)*self._superRowSizeInBytes)])
            else:
                imgBot.extend(rawData[(j*self._superRowSizeInBytes):((j+1)*self._superRowSizeInBytes)]) 
        imgDesc = imgTop
        imgDesc.extend(imgBot)

        # returns final image
        return imgDesc

    def _descrambleEPix100aImage(self, rawData):
        """performs the ePix100a image descrambling """
        
        imgDescBA = self._descrambleEPix100aImageAsByteArray(rawData)

        imgDesc = np.frombuffer(imgDescBA,dtype='int16')
        if self.sensorHeight*self.sensorWidth != len(imgDesc):
           print("Got wrong pixel number ", len(imgDesc))
        else:
           if (PRINT_VERBOSE): print("Got pixel number ", len(imgDesc))
           imgDesc = imgDesc.reshape(self.sensorHeight, self.sensorWidth)
        # returns final image
        return imgDesc

    def _descrambleTixel48x48Image(self, rawData):
        """performs the Tixel image descrambling """
        if (len(rawData)==4):
            ##if (PRINT_VERBOSE): print('raw data 0:', rawData[0,0:10])
            ##if (PRINT_VERBOSE): print('raw data 1:', rawData[1,0:10])
            ##if (PRINT_VERBOSE): print('raw data 2:', rawData[2,0:10])
            ##if (PRINT_VERBOSE): print('raw data 3:', rawData[3,0:10])
            
            quadrant0 = np.frombuffer(rawData[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(48,48)
            quadrant1 = np.frombuffer(rawData[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(48,48)
            quadrant2 = np.frombuffer(rawData[2,4:],dtype='uint16')
            quadrant2sq = quadrant2.reshape(48,48)
            quadrant3 = np.frombuffer(rawData[3,4:],dtype='uint16')
            quadrant3sq = quadrant3.reshape(48,48)
        
            imgTop = np.concatenate((quadrant0sq, quadrant1sq),1)
            imgBot = np.concatenate((quadrant2sq, quadrant3sq),1)

            imgDesc = np.concatenate((imgTop, imgBot),0)
        else:
            imgDesc = np.zeros((48*2,48*2), dtype='uint16')
        # returns final image
        imgDesc = np.where((imgDesc & 0x1) == 1 , imgDesc, 0)
        return imgDesc


    # helper functions
    def _calcImgWidth(self):
        return self._NumAsicsPerSide * self._NumAdcChPerAsic * self._NumColPerAdcCh

