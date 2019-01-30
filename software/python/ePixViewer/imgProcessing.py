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


import sys
import os
import rogue.utilities
import rogue.utilities.fileio
import rogue.interfaces.stream
import pyrogue    
import time
import numpy as np

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *

PRINT_VERBOSE = 0

################################################################################
################################################################################
#   Image processing class
#   
################################################################################
class ImageProcessing():
    """implements basic image processing specific to the SLAC cameras"""

    # define global properties
    imgHeight = 706
    imgNumAsicsPerSide = 2
    imgNumAdcChPerAsic = 4
    imgNumColPerAdcCh = 96
    superRowSize = 384
    superRowSizeInBytes = superRowSize * 4 # 4 bytes per asic word

    # variables to perform some initial image processing
    numDarkImages = 10
    numSavedDarkImg = 0
    imgDark = np.array([],dtype='uint16')
    _imgDarkSet = np.array([],dtype='uint16')
    imgDark_isSet = False
    imgDark_isRequested = False


    def __init__(self, parent) :
        # pointer to the parent class        
        self.parent = parent
        # init compound variables
        self.calcImgWidth()
        # creates the placehold for the dark images to be stored
        self.createDarkImageSet()

    def calcImgWidth(self):
        self.imgWidth = self.imgNumAsicsPerSide * self.imgNumAdcChPerAsic * self.imgNumColPerAdcCh      

    def createDarkImageSet(self):
        self._imgDarkSet = np.zeros([self.numDarkImages,self.imgHeight,self.imgWidth],dtype='uint16')

    def setDarkImg(self, rawData):
        """performs the ePix100A image descrambling"""
        #init variable that tells dark image was requested
        if (self.numSavedDarkImg == 0):
            self.createDarkImageSet()
            self.imgDark_isRequested = True
        # save the set
        self._imgDarkSet[self.numSavedDarkImg,:,:] = np.array(rawData,dtype='uint16')
        self.numSavedDarkImg = self.numSavedDarkImg + 1
        #checks for end condition
        if (self.numSavedDarkImg == self.numDarkImages):
            self.imgDark = np.average(self._imgDarkSet,axis=0)
            self.imgDark_isSet = True
            self.imgDark_isRequested = False
            self.numSavedDarkImg = 0
            print("Dark image set.")

    def unsetDarkImg(self):
        """performs the ePix100A image descrambling"""
        self.imgDark_isSet = False

    def getDarkSubtractedImg(self, rawImg):
        return rawImg - self.imgDark

    def reScaleImgTo8bit(self, rawImage, scaleMax=20000, scaleMin=-200):
        #init
        image = np.clip(rawImage, scaleMin, scaleMax)
        
        #re-scale
        deltaScale = abs(scaleMax - scaleMin)
        if (deltaScale == 0):
            deltaScale = 1
        imageRS = np.array(((image-scaleMin) * (255 / (deltaScale))))     
        image8b = imageRS.astype('uint8')

        #return results
        return image8b

    """Uses the bitwise and function to apply a bit mask into the descrabled image"""
    def applyBitMask(self, image, mask = 0xFFFF):
        return np.bitwise_and(image, mask)

