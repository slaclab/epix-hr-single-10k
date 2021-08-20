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
#import rogue.utilities
#import rogue.utilities.fileio
#import rogue.interfaces.stream
#import pyrogue    
import time
import numpy as np
import ePixViewer.imgProcessing as imgPr

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *

# define global constants
NOCAMERA   = 0
EPIX100A   = 1
EPIX100P   = 2
TIXEL48X48 = 3
EPIX10KA   = 4
CPIX2      = 5
EPIXM32    = 6
HRADC32x32 = 7
CRYO64XN   = 8
EPIXMNX64  = 9
EPIXHR10kT = 10


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
    availableCameras = {  'ePix100a':  EPIX100A, 'ePix100p' : EPIX100P, 'Tixel48x48' : TIXEL48X48, 'ePix10ka' : EPIX10KA,  'Cpix2' : CPIX2, 'ePixM32Array' : EPIXM32, 'HrAdc32x32': HRADC32x32, 'cryo64xN':  CRYO64XN, 'ePixHrePixM' : EPIXMNX64, 'ePixHr10kT': EPIXHR10kT }
    

    def __init__(self, cameraType = 'ePix100a', verbose=False) :
        
        camID = self.availableCameras.get(cameraType, NOCAMERA)
        self.Verbose = verbose

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
        if (camID == CPIX2):
            self._initCpix2()
        if (camID == EPIXM32):
            self._initEpixM32()
        if (camID == HRADC32x32):
            self._initEpixHRADC32x32()
        if (camID == CRYO64XN):
            self._initCRYO64XN()
        if (camID == EPIXMNX64):
            self._initEPIXMNX64()
        if (camID == EPIXHR10kT):
            self._initEPIXHR10kT()

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
        if (camID == CPIX2):
            descImg = self._descrambleCpix2Image(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == EPIXM32):
            descImg = self._descrambleEpixM32Image(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == HRADC32x32):
            descImg = self._descrambleEpixHRADC32x32Image(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == CRYO64XN):
            descImg = self._descrambleCRYO64XNImage(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == EPIXMNX64):
            descImg = self._descrambleEPIXMNX64Image(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)
        if (camID == EPIXHR10kT):
            descImg = self._descrambleEpixHR10kTImage(rawData)
            return self.imgTool.applyBitMask(descImg, mask = self.bitMask)

        if (camID == NOCAMERA):
            return Null

    # return
    def buildImageFrame(self, currentRawData, newRawData):
        camID = self.availableCameras.get(self.cameraType, NOCAMERA)

        if (self.Verbose): print('buildImageFrame - camID: ', camID)

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
        if (camID == CPIX2):
            #Needs to check the two frames and make a decision on the flags
            [frameComplete, readyForDisplay, newRawData]  = self._buildFrameCpix2Image(currentRawData, newRawData)
            return [frameComplete, readyForDisplay, newRawData]
            print('end of buildImageFrame')
        if (camID == EPIXM32):
            [frameComplete, readyForDisplay, newRawData]  = self._buildFrameEpixM32Image(currentRawData, newRawData)
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == HRADC32x32):
            [frameComplete, readyForDisplay, newRawData]  = self._buildFrameEpixHRADC32x32Image(currentRawData, newRawData)
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == CRYO64XN):
            # The flags are always true since each frame holds an entire image
            frameComplete = 1
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == EPIXMNX64):
            # The flags are always true since each frame holds an entire image
            frameComplete = 1
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, newRawData]
        if (camID == EPIXHR10kT):
            frameComplete = 1
            readyForDisplay = 1
            #[frameComplete, readyForDisplay, newRawData]  = self._buildFrameEpix10kTImage(currentRawData, newRawData)
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

    def _initCpix2(self):
        #self._superRowSize = 384
        self._NumAsicsPerSide = 1
        #self._NumAdcChPerAsic = 4
        #self._NumColPerAdcCh = 96
        #self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth  = 96 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.sensorHeight = 96 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.pixelDepth = 16
        self.bitMask = np.uint16(0x7FFF)
   
    def _initEpixM32(self):
        #self._superRowSize = 384
        self._NumAsicsPerSide = 1
        #self._NumAdcChPerAsic = 4
        #self._NumColPerAdcCh = 96
        #self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth  = 64 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.sensorHeight = 64 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.pixelDepth = 16
        self.bitMask = np.uint16(0x3FFF)
    def _initEpixHRADC32x32(self):
        #self._superRowSize = 384
        self._NumAsicsPerSide = 1
        #self._NumAdcChPerAsic = 4
        #self._NumColPerAdcCh = 96
        #self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth  = 64 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.sensorHeight = 32 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.pixelDepth = 16
        self.bitMask = np.uint16(0xFFFF)

    def _initCRYO64XN(self):
        self._NumAsicsPerSide = 1
        self._NumChPerAsic = 64
        self._Header_Length = 6
        self.pixelDepth = 16
        self.cameraModule = "Single ASIC CRYO"
        self.bitMask = np.uint16(0xFFFF)

    def _initEPIXMNX64(self):
        self._NumAsicsPerSide = 1
        self._NumChPerAsic = 64
        self._Header_Length = 6
        self.pixelDepth = 16
        self.cameraModule = "Single ASIC CRYO"
        self.bitMask = np.uint16(0xFFFF)

    def _initEPIXHR10kT(self):
        #self._superRowSize = 384
        self._NumAsicsPerSide = 1
        #self._NumAdcChPerAsic = 4
        #self._NumColPerAdcCh = 96
        #self._superRowSizeInBytes = self._superRowSize * 4
        self.sensorWidth  = 192 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.sensorHeight = 146 # The sensor size in this dimension is doubled because each pixel has two information (ToT and ToA) 
        self.pixelDepth = 16
        self.bitMask = np.uint16(0xFFFF)

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

        
        ##if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        ##if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        isTOA_newRawData   = (newRawData_DW[2] & 0x8) >> 3        # header dword 2  
        asicNum_newRawData =  newRawData_DW[2] & 0x7              # header dword 2
        ##if (self.Verbose): print('\nacqNum_newRawData: ', acqNum_newRawData, '\nisTOA_newRawData:', isTOA_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)


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
            if (self.Verbose): print('\n packet size error, packet len: ', len(currentRawData))

        ##if (self.Verbose): print('\nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        ##if (self.Verbose): print('\nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]

        #fill the memory with the new data (when acqNums matches)
        returnedRawData = self.fill_memory(returnedRawData, asicNum_newRawData, isTOA_newRawData, newRawData_DW)
        if (self.Verbose): print('Return data 0:', returnedRawData[0,0:10])
        if (self.Verbose): print('Return data 1:', returnedRawData[1,0:10])
        if (self.Verbose): print('Return data 2:', returnedRawData[2,0:10])
        if (self.Verbose): print('Return data 3:', returnedRawData[3,0:10])

        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        if (self.Verbose): print('\nisValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        if (self.Verbose): print('\nisValidTrace1', isValidTrace1)
        isValidTrace2 =  returnedRawData[2,0]
        if (self.Verbose): print('\nisValidTrace2', isValidTrace2)
        isValidTrace3 =  returnedRawData[3,0]
        if (self.Verbose): print('\nisValidTrace3', isValidTrace3)

        if((isValidTrace0 == 1) and (isValidTrace1 == 1) and (isValidTrace2 == 1) and (isValidTrace3 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0

        if (self.Verbose): print('frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]

    def _buildFrameCpix2Image(self, currentRawData, newRawData):
        """ Performs the Cpix2 frame building.
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

        
        if (self.Verbose): print('\n0 \nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        if (self.Verbose): print('\n1 \nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        isTOA_newRawData   = (newRawData_DW[2] & 0x8) >> 3        # header dword 2  
        asicNum_newRawData =  newRawData_DW[2] & 0x7              # header dword 2
        if (self.Verbose): print('\n2 \n acqNum_newRawData: ', acqNum_newRawData, '\nisTOA_newRawData:', isTOA_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)


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
        elif((len(currentRawData) == 1155) or (len(currentRawData) == 4620)):
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

            if (self.Verbose): print('\n3 \n Return data 0:', returnedRawData[0,0:10])
            if (self.Verbose): print('\n3 \n Return data 1:', returnedRawData[1,0:10])
            if (self.Verbose): print('\n3 \n Return data 2:', returnedRawData[2,0:10])
            if (self.Verbose): print('\n3 \n Return data 3:', returnedRawData[3,0:10])
        
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
            if (self.Verbose): print('\n3B \n len 4')
            returnedRawData = currentRawData
        else:
            #packet size error
            if (self.Verbose): print('\n4  \npacket size error, packet len: ', len(currentRawData))

        if (self.Verbose): print('\n5 \nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        if (self.Verbose): print('\n5 \nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]

        #fill the memory with the new data (when acqNums matches)
        returnedRawData = self.fill_memory(returnedRawData, asicNum_newRawData, isTOA_newRawData, newRawData_DW)
        if (self.Verbose): print('\n6 \nReturn data 0:', returnedRawData[0,0:10])
        if (self.Verbose): print('\n6 \nReturn data 1:', returnedRawData[1,0:10])
        if (self.Verbose): print('\n6 \nReturn data 2:', returnedRawData[2,0:10])
        if (self.Verbose): print('\n6 \nReturn data 3:', returnedRawData[3,0:10])

        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        if (self.Verbose): print('\n7 \nisValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        if (self.Verbose): print('\n8 \nisValidTrace1', isValidTrace1)
        isValidTrace2 =  returnedRawData[2,0]
        if (self.Verbose): print('\n9 \nisValidTrace2', isValidTrace2)
        isValidTrace3 =  returnedRawData[3,0]
        if (self.Verbose): print('\n10 \nisValidTrace3', isValidTrace3)

        if((isValidTrace0 == 1) and (isValidTrace1 == 1) and (isValidTrace2 == 1) and (isValidTrace3 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0

        if (self.Verbose): print('\n11 \nframeComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]
    
    #fill the memory with the new data (when acqNums matches)
    def fill_memory(self, returnedRawData, asicNum_currentRawData, isTOA_currentRawData, newRawData_DW):
        ##if (self.Verbose): print('New data:', newRawData_DW[0:10])
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
            ##if (self.Verbose): print('Return data 0:', returnedRawData[0,0:10])
            ##if (self.Verbose): print('Return data 1:', returnedRawData[1,0:10])
            ##if (self.Verbose): print('Return data 2:', returnedRawData[2,0:10])
            ##if (self.Verbose): print('Return data 3:', returnedRawData[3,0:10])
        return returnedRawData


    def _buildFrameEpixM32Image(self, currentRawData, newRawData):
        """ Performs the epixM32 frame building.
            For this sensor the image takes two frames
            There is no guarantee both frames will always arrive nor on their order."""
        #init local variables
        frameComplete = 0
        readyForDisplay = 0
        returnedRawData = []
        acqNum_currentRawData  = 0
        asicNum_currentRawData = 0
        acqNum_newRawData  = 0
        asicNum_newRawData = 0

        
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        asicNum_newRawData =  newRawData_DW[2] & 0xF              # header dword 2
        #if (self.Verbose): print('\nacqNum_newRawData: ', acqNum_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)
        
        #for i in range(3, 10):
        #    print('New %x %x' %(newRawData_DW[i]&0xFFFF, newRawData_DW[i]>>16))
        

        #interpret headers
        #case 1: new image (which means currentRawData is empty)
        if (len(currentRawData) == 0):
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((1028,),dtype='uint32')# 2054 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        #case where the currentRawData is a byte array
        elif(len(currentRawData) == 4108):
            #for i in range(3, 10):
            #    print('Curr %x %x' %(currentRawData[i]&0xFFFF, currentRawData[i]>>16))
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((1028,),dtype='uint32')# 2054 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        
        elif(len(currentRawData)==2):
            #for i in range(3, 10):
            #    print('Cur0 %x %x' %(currentRawData[0,i]&0xFFFF, currentRawData[0,i]>>16))
            #for i in range(3, 10):
            #    print('Cur1 %x %x' %(currentRawData[1,i]&0xFFFF, currentRawData[1,i]>>16))
            
            #recovers currentRawData header info
            #loop traverses the four traces to find the info
            for j in range(0,2):
                #print(len(currentRawData))
                if(currentRawData[j,0]==1):
                                                                                # extended header dword 0 (valid trace)
                                                                                # extended header dword 1 (VC info)
                    acqNum_currentRawData  =  currentRawData[j,2]               # extended header dword 2 (acq num)
                    asicNum_currentRawData =  currentRawData[j,3] & 0xf         # extended header dword 1 (VC info)
            #saves current data on returned data before adding new data
            returnedRawData = currentRawData
        else:
            #packet size error
            if (self.Verbose): print('\n packet size error, packet len: ', len(currentRawData))

        ##if (self.Verbose): print('\nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        ##if (self.Verbose): print('\nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]
        
        #fill the memory with the new data (when acqNums matches)
        if (len(newRawData_DW)==1027):
            if(asicNum_newRawData==0):
                returnedRawData[0,0]  = 1
                returnedRawData[0,1:] = newRawData_DW
            if(asicNum_newRawData==1):
                returnedRawData[1,0]  = 1
                returnedRawData[1,1:] = newRawData_DW
        
        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        ##if (self.Verbose): print('\nisValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        ##if (self.Verbose): print('\nisValidTrace1', isValidTrace1)
        if((isValidTrace0 == 1) and (isValidTrace1 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0
        
        #if (self.Verbose): print('frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]



    def _buildFrameEpixHRADC32x32Image(self, currentRawData, newRawData):
        """ Performs the epixHRADC32x32 frame building.
            For this sensor the image takes two frames
            There is no guarantee both frames will always arrive nor on their order."""
        #init local variables
        frameComplete = 0
        readyForDisplay = 0
        returnedRawData = []
        acqNum_currentRawData  = 0
        asicNum_currentRawData = 0
        acqNum_newRawData  = 0
        asicNum_newRawData = 0

        
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        asicNum_newRawData =  newRawData_DW[2] & 0x7              # header dword 2
        #if (self.Verbose): print('\nacqNum_newRawData: ', acqNum_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)
        
        #for i in range(3, 10):
        #    print('New %x %x' %(newRawData_DW[i]&0xFFFF, newRawData_DW[i]>>16))
        

        #interpret headers
        #case 1: new image (which means currentRawData is empty)
        if (len(currentRawData) == 0):
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((516,),dtype='uint32')# 512 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        #case where the currentRawData is a byte array
        elif(len(currentRawData) == 2060):
            #for i in range(3, 10):
            #    print('Curr %x %x' %(currentRawData[i]&0xFFFF, currentRawData[i]>>16))
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((516,),dtype='uint32')# 512 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        
        elif(len(currentRawData)==2):
            #for i in range(3, 10):
            #    print('Cur0 %x %x' %(currentRawData[0,i]&0xFFFF, currentRawData[0,i]>>16))
            #for i in range(3, 10):
            #    print('Cur1 %x %x' %(currentRawData[1,i]&0xFFFF, currentRawData[1,i]>>16))
            
            #recovers currentRawData header info
            #loop traverses the four traces to find the info
            for j in range(0,2):
                print("_buildFrameEpixHRADC32x32Image",len(currentRawData))
                if(currentRawData[j,0]==1):
                                                                                # extended header dword 0 (valid trace)
                                                                                # extended header dword 1 (VC info)
                    acqNum_currentRawData  =  currentRawData[j,2]               # extended header dword 2 (acq num)
                    asicNum_currentRawData =  currentRawData[j,3] & 0x7         # extended header dword 1 (VC info)
            #saves current data on returned data before adding new data
            returnedRawData = currentRawData
        else:
            #packet size error
            if (self.Verbose): print('\n_buildFrameEpixHRADC32x32Image: packet size error, packet len: ', len(currentRawData))

        ##if (self.Verbose): print('\nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        ##if (self.Verbose): print('\nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]
        
        #fill the memory with the new data (when acqNums matches)
        if (len(newRawData_DW)==515):
            if(asicNum_newRawData==0 or asicNum_newRawData==2):
                returnedRawData[0,0]  = 1
                returnedRawData[0,1:] = newRawData_DW
            if(asicNum_newRawData==1):
                returnedRawData[1,0]  = 1
                returnedRawData[1,1:] = newRawData_DW
        
        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        if (self.Verbose): print('\n_buildFrameEpixHRADC32x32Image: isValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        if (self.Verbose): print('\n_buildFrameEpixHRADC32x32Image: isValidTrace1', isValidTrace1)
        if((isValidTrace0 == 1) and (isValidTrace1 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0
        
        if (self.Verbose): print('_buildFrameEpixHRADC32x32Image: frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]


    def _buildFrameEpix10kTImage(self, currentRawData, newRawData):
        """ Performs the epixM32 frame building.
            For this sensor the image takes two frames
            There is no guarantee both frames will always arrive nor on their order."""
        #init local variables
        frameComplete = 0
        readyForDisplay = 0
        returnedRawData = []
        acqNum_currentRawData  = 0
        asicNum_currentRawData = 0
        acqNum_newRawData  = 0
        asicNum_newRawData = 0

        
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data', len(newRawData))
        #converts data to 32 bit 
        newRawData_DW = np.frombuffer(newRawData,dtype='uint32')
        #if (self.Verbose): print('\nlen current Raw data', len(currentRawData), 'len new raw data DW', len(newRawData_DW))

        #retrieves header info
                                                                  # header dword 0 (VC info)
        acqNum_newRawData  =  newRawData_DW[1]                    # header dword 1
        asicNum_newRawData =  newRawData_DW[2] & 0xF              # header dword 2
        if (self.Verbose): print('\nacqNum_newRawData: ', acqNum_newRawData, '\nasicNum_newRawData:', asicNum_newRawData)
        
        #for i in range(3, 10):
        #    print('New %x %x' %(newRawData_DW[i]&0xFFFF, newRawData_DW[i]>>16))
        

        #interpret headers
        #case 1: new image (which means currentRawData is empty)
        if (len(currentRawData) == 0):
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((14029,),dtype='uint32')# 2054 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        #case where the currentRawData is a byte array
        elif(len(currentRawData) == 56112):
            for i in range(3, 10):
                print('Curr %x %x' %(currentRawData[i]&0xFFFF, currentRawData[i]>>16))
            frameComplete = 0
            readyForDisplay = 0
            z = np.zeros((14029,),dtype='uint32')# 2054 for the package plus 1 (first byte for the valid flag 
            returnedRawData = np.array([z,z])
            
            #makes the current raw data info the same as new so the logic later on this function will add the new data to the memory
            acqNum_currentRawData  = acqNum_newRawData
            asicNum_currentRawData = asicNum_newRawData
        
        elif(len(currentRawData)==2):
            #for i in range(3, 10):
            #    print('Cur0 %x %x' %(currentRawData[0,i]&0xFFFF, currentRawData[0,i]>>16))
            #for i in range(3, 10):
            #    print('Cur1 %x %x' %(currentRawData[1,i]&0xFFFF, currentRawData[1,i]>>16))
            
            #recovers currentRawData header info
            #loop traverses the four traces to find the info
            for j in range(0,2):
                #print(len(currentRawData))
                if(currentRawData[j,0]==1):
                                                                                # extended header dword 0 (valid trace)
                                                                                # extended header dword 1 (VC info)
                    acqNum_currentRawData  =  currentRawData[j,2]               # extended header dword 2 (acq num)
                    asicNum_currentRawData =  currentRawData[j,3] & 0xf         # extended header dword 1 (VC info)
            #saves current data on returned data before adding new data
            returnedRawData = currentRawData
        else:
            #packet size error
            if (self.Verbose): print('\n packet size error, packet len: ', len(currentRawData))

        ##if (self.Verbose): print('\nacqNum_currentRawData: ', acqNum_currentRawData, '\nisTOA_currentRawData: ', isTOA_currentRawData, '\nasicNum_currentRawData: ', asicNum_currentRawData)
        ##if (self.Verbose): print('\nacqNum_newRawData: ',     acqNum_newRawData,     '\nisTOA_newRawData: ',     isTOA_newRawData, '\nasicNum_newRawData: ', asicNum_newRawData)
        #case 2: acqNumber are different
        if(acqNum_newRawData != acqNum_currentRawData):
            frameComplete = 0
            readyForDisplay = 1
            return [frameComplete, readyForDisplay, currentRawData]
        
        #fill the memory with the new data (when acqNums matches)
        if (len(newRawData_DW)==1027):
            if(asicNum_newRawData==0):
                returnedRawData[0,0]  = 1
                returnedRawData[0,1:] = newRawData_DW
            if(asicNum_newRawData==1):
                returnedRawData[1,0]  = 1
                returnedRawData[1,1:] = newRawData_DW
        
        #checks if the image is complete
        isValidTrace0 =  returnedRawData[0,0]
        ##if (self.Verbose): print('\nisValidTrace0', isValidTrace0)
        isValidTrace1 =  returnedRawData[1,0]
        ##if (self.Verbose): print('\nisValidTrace1', isValidTrace1)
        if((isValidTrace0 == 1) and (isValidTrace1 == 1)):
            frameComplete = 1
            readyForDisplay = 1
        else:
            frameComplete = 0
            readyForDisplay = 0
        
        #if (self.Verbose): print('frameComplete: ', frameComplete, 'readyForDisplay: ', readyForDisplay, 'returned raw data len', len(returnedRawData))
        #return parameters
        return [frameComplete, readyForDisplay, returnedRawData]    

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
           if (self.Verbose): print("Got pixel number ", len(imgDesc))
           imgDesc = imgDesc.reshape(self.sensorHeight, self.sensorWidth)
        # returns final image
        return imgDesc

    def _descrambleTixel48x48Image(self, rawData):
        """performs the Tixel image descrambling """
        if (len(rawData)==4):
            if (self.Verbose): print('raw data 0:', rawData[0,0:10])
            if (self.Verbose): print('raw data 1:', rawData[1,0:10])
            if (self.Verbose): print('raw data 2:', rawData[2,0:10])
            if (self.Verbose): print('raw data 3:', rawData[3,0:10])
            
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

    def _descrambleCpix2Image(self, rawData):
        """performs the Tixel image descrambling """
        if (len(rawData)==4):
            ##if (self.Verbose): print('raw data 0:', rawData[0,0:10])
            ##if (self.Verbose): print('raw data 1:', rawData[1,0:10])
            ##if (self.Verbose): print('raw data 2:', rawData[2,0:10])
            ##if (self.Verbose): print('raw data 3:', rawData[3,0:10])
            
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
        
        return imgDesc
        
    def _descrambleEpixM32Image(self, rawData):
        """performs the EpixM32 image descrambling """
        if (len(rawData)==2):
            #if (self.Verbose): print('raw data 0:', rawData[0,0:10])
            #if (self.Verbose): print('raw data 1:', rawData[1,0:10])
            
            quadrant0 = np.frombuffer(rawData[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(64,32)
            quadrant1 = np.frombuffer(rawData[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(64,32)
        
            imgTop = quadrant0sq
            imgBot = quadrant1sq

            imgDesc = np.concatenate((imgTop, imgBot),1)
        else:
            imgDesc = np.zeros((64,64), dtype='uint16')
        # returns final image
        return imgDesc

    def _descrambleEpixHRADC32x32Image(self, rawData):
        """performs the EpixM32 image descrambling """
        if (len(rawData)==2):
            if (self.Verbose): print('_descrambleEpixHRADC32x32Image: raw data 0:', rawData[0,0:10])
            if (self.Verbose): print('_descrambleEpixHRADC32x32Image: raw data 1:', rawData[1,0:10])
            
            quadrant0 = np.frombuffer(rawData[0,4:],dtype='uint16')
            quadrant0sq = quadrant0.reshape(32,32)
            quadrant1 = np.frombuffer(rawData[1,4:],dtype='uint16')
            quadrant1sq = quadrant1.reshape(32,32)
        
            imgTop = quadrant0sq
            imgBot = quadrant1sq

            imgDesc = np.concatenate((imgTop, imgBot),1)
        else:
            imgDesc = np.zeros((32,64), dtype='uint16')
            print("_descrambleEpixHRADC32x32Image: Wrong number of buffers. Returning zeros")
        # returns final image
        return imgDesc

    def _descrambleCRYO64XNImage(self, rawData):
        """performs a single Cryo ASIC image descrambling """

        if (type(rawData != 'numpy.ndarray')):
            img = np.frombuffer(rawData,dtype='uint16')
                
        print("Incoming data shape", img.shape)
                
        #calculate number of samples
        samples = int((img.shape[0]-self._Header_Length)/self._NumChPerAsic)

        if (samples) != ((img.shape[0]-self._Header_Length)/self._NumChPerAsic):
            imgDesc = np.zeros((self._NumChPerAsic,self._NumChPerAsic), dtype='uint16')
            print("_descrambleEpixHRADC32x32Image: Wrong data length, Returning zeros. Data length: ", (img.shape[0]-self._Header_Length))
            return imgDesc

        #remove header
        img2 = img[self._Header_Length:].reshape(samples,self._NumChPerAsic)

        #descramble image
        imgDesc = np.append(img2[:,0:self._NumChPerAsic:2].transpose(), img2[:,1:self._NumChPerAsic:2].transpose()).reshape(self._NumChPerAsic,samples)
        
        # returns final image
        return imgDesc

    def _descrambleEPIXMNX64Image(self, rawData):
        """performs a single Cryo ASIC image descrambling """

        if (type(rawData != 'numpy.ndarray')):
            img = np.frombuffer(rawData,dtype='uint16')
                
        print("Incoming data shape", img.shape)
                
        #calculate number of samples
        samples = int((img.shape[0]-self._Header_Length)/self._NumChPerAsic)

        if (samples) != ((img.shape[0]-self._Header_Length)/self._NumChPerAsic):
            imgDesc = np.zeros((self._NumChPerAsic,self._NumChPerAsic), dtype='uint16')
            print("_descramble EPIXMNX64 Image: Wrong data length, Returning zeros. Data length: ", (img.shape[0]-self._Header_Length))
            return imgDesc

        #remove header
        img2 = img[self._Header_Length:].reshape(samples,self._NumChPerAsic)

        #descramble image
        imgDesc = np.append(img2[:,0:self._NumChPerAsic:2].transpose(), img2[:,1:self._NumChPerAsic:2].transpose()).reshape(self._NumChPerAsic,samples)
        
        # returns final image
        return np.transpose(imgDesc)

    def _descrambleEpixHR10kTImage(self, rawData):
        """performs the Epix10kT image descrambling """
        if (self.Verbose):print("Length raw data: %d" % (len(rawData)))
        if (len(rawData)==56076):
             if (type(rawData != 'numpy.ndarray')):
                img = np.frombuffer(rawData,dtype='uint16')
             if (self.Verbose):print("shape", img.shape)          
             #Select data payload
             quadrant0 = np.frombuffer(img[6:28038],dtype='uint16')
             #descramble image
             #get data for each bank
             adcImg = quadrant0.reshape(-1,6)
             for i in range(0,6):
                 #reshape data into 2D array per bank
                 adcImg2 = adcImg[0:adcImg.shape[0],i].reshape(-1,32)
                 #apply row-shift patch
                 adcImg2[1:,30] = adcImg2[0:adcImg2.shape[0]-1,30]
                 adcImg2[1:,31] = adcImg2[0:adcImg2.shape[0]-1,31]
                 #concatenate bank data into a single image per asic
                 if i == 0:
                     quadrant0sq = adcImg2
                 else:
                     quadrant0sq = np.concatenate((quadrant0sq,adcImg2),1)
             imgDesc = quadrant0sq
        else:
            print("descramble error")
            imgDesc = np.zeros((144,384), dtype='uint16')
            
        # returns final image
        return imgDesc

    # helper functions
    def _calcImgWidth(self):
        return self._NumAsicsPerSide * self._NumAdcChPerAsic * self._NumColPerAdcCh
