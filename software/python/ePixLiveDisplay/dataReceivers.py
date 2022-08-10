#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Updated data receivers for PyDM live viewer
#-----------------------------------------------------------------------------
# File       : dataReceivers.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-07-27
#-----------------------------------------------------------------------------
# Description:
# Updated data receivers for processing image, environment, and pseudoscope
# data for the new PyDM live viewer
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import pyrogue as pr
import numpy as np
import sys
import collections
import time
from copy import copy

class DataReceiverEpixHrSingle10kT(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Queue = collections.deque(maxlen = 50000)
        # Queue for histogram
        self.ImageQueue = collections.deque(maxlen = 30)
        # Queue for automatic contrast
        self.NoiseQueue = collections.deque(maxlen = 1000)
        # Queue for noise color map
        self.numDarkCol = 0
        self.DarkImg = []
        self.oldApplyDark = False
        self.x = 0
        self.y = 0
        self.start = time.time()
        self.colormap = []
        self.add(pr.LocalVariable(
            name = "PixelData",
            value = 0,
            mode = "RO",
            description = "Scalar pixel value for timeplot"
        ))
        self.add(pr.LocalVariable(
            name = "X",
            value = 0,
            description = "Cursor coordinate"
        ))
        self.add(pr.LocalVariable(
            name = "Y",
            value = 0,
            description = "Cursor coordinate"
        ))
        self.add(pr.LocalVariable(
            name = "NumDarkReq",
            value = 0,
            description = "Number of dark requested"
        ))
        self.add(pr.LocalVariable(
            name = "NumDarkCol",
            value = 0,
            description = "Number of dark collected"
        ))
        self.add(pr.LocalVariable(
            name = "ApplyDark",
            value = False,
            description = "Whether to apply dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "DarkReady",
            value = False,
            description = "Whether dark is ready or not"
        ))
        self.add(pr.LocalVariable(
            name = "CollectDark",
            value = False,
            description = "Whether user wants to collect dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "AvgDark",
            value = np.empty([146,192]),
            description = "Average of darks collected,"
        ))
        self.add(pr.LocalVariable(
            name = "ShowDark",
            value = False,
            description = "Whether to show dark or not"
        ))
        self.add(pr.LocalVariable(
            name = "MaxPixVal",
            value = 12000,
            description = "Maximum contrast"
        ))
        self.add(pr.LocalVariable(
            name = "MinPixVal",
            value = 10000,
            description = "Minimum contrast"
        ))
        self.add(pr.LocalVariable(
            name = "Histogram",
            value = [],
            description = "Vector data for histogram's y-axis"
        ))
        self.add(pr.LocalVariable(
            name = "Bins",
            value = [],
            description = "Vector data for histogram's bins"
        ))
        self.add(pr.LocalVariable(
            name = "PlotHorizontal",
            value = False,
            description = "Whether to plot horizontal rows or not"
        ))
        self.add(pr.LocalVariable(
            name = "PlotVertical",
            value = False,
            description = "Whether to plot vertical columns or not"
        ))
        self.add(pr.LocalVariable(
            name = "Horizontal",
            value = [],
            description = "Vector data for horizontal row pixel values"
        ))
        self.add(pr.LocalVariable(
            name = "Vertical",
            value = [],
            description = "Vector data for vertical column pixel values"
        ))
        self.add(pr.LocalVariable(
            name = "AutoCon",
            value = False,
            description = "Whether to have auto contrast or not"
        ))
        self.add(pr.LocalVariable(
            name = "DescError",
            value = 0,
            mode = "RO",
            description = "Count of descramble errors to be displayed"
        ))
        self.add(pr.LocalVariable(
            name = "NoiseColormap",
            value = False,
            description = "Whether to show noise colormap or not"
        ))
        self.add(pr.LocalVariable(
            name = "NoiseColormapReady",
            value = False,
            description = "Whether NoiseColormap is ready or not"
        ))

    def descramble(self, frame):
        # Function to descramble raw frames into numpy arrays
        img = frame.getNumpy(0, frame.getPayload()).view(np.uint16)
        quadrant0 = img[6:28038]
        adcImg = quadrant0.reshape(-1,6)
        for i in range(0,6):
            if len(adcImg[0:adcImg.shape[0],i]) == 4672:
                adcImg2 = adcImg[0:adcImg.shape[0],i].reshape(-1,32)
                adcImg2[1:,30] = adcImg2[0:adcImg2.shape[0]-1,30]
                adcImg2[1:,31] = adcImg2[0:adcImg2.shape[0]-1,31]
                if i == 0:
                    quadrant0sq = adcImg2
                else:
                    quadrant0sq = np.concatenate((quadrant0sq,adcImg2),1)
            else:
                self.DescError.set(self.DescError.get() + 1, write = True)
                raise Exception("*****Descramble error*****")
        return quadrant0sq

    def process(self, frame):
        if time.time() - self.start > 1 and self.NoiseQueue:
            self.start = time.time()
            self.colormap = np.std(np.array(self.NoiseQueue), 0)
            print(len(self.NoiseQueue))
        if len(self.colormap):
            self.NoiseColormapReady.set(True, write = True)
        with self.root.updateGroup():
            imgDesc = self.descramble(frame)
            imgView = copy(imgDesc)
            imgRaw = copy(imgDesc)

            # Dark collecting process:
            if self.CollectDark.get():
                if self.DarkReady.get():
                    self.AvgDark.set(np.empty([146,192]), write = True)
                    self.DarkImg = []
                    self.DarkReady.set(False, write = True)
                    self.numDarkCol = 0
                if self.NumDarkReq.get() is not self.numDarkCol:
                    self.DarkImg.append(imgRaw)
                    self.numDarkCol += 1
                else:
                    self.AvgDark.set(np.mean(np.array(np.intc(self.DarkImg)),axis=0), write = True)
                    self.DarkReady.set(True, write = True)
                    print("\n*****Dark ready*****\n")
                    self.CollectDark.set(False, write = True)
            if self.ApplyDark.get() is not self.oldApplyDark:
                self.Queue = []
                self.ImageQueue = []
                self.NoiseQueue = []
                self.oldApplyDark = self.ApplyDark.get()
            if self.ApplyDark.get():
                imgView = np.intc(imgView) - self.AvgDark.get()
                imgRaw = np.intc(imgRaw) - self.AvgDark.get()
            if self.ShowDark.get():
                self.Data.set(self.AvgDark.get(), write = True)
            else:
                if int(self.X.get()) is not self.y or int(self.Y.get()) is not self.x:
                    self.Queue = []

                # Switch x and y due to PyDMImageViewer row-coloumn switching:
                self.y = int(self.X.get())
                self.x = int(self.Y.get())

                if self.NoiseColormap.get():
                    imgView = copy(self.colormap)
                # Showing crosshair:
                crossHairVal = -sys.maxsize - 1
                for i in range(self.x - 10, self.x + 10):
                    if i >= 0 and i < 146 and self.x > 0 and self.x < 146 and self.y - 1 > 0 and self.y + 1 < 192:
                        imgView[i][self.y] = crossHairVal
                        imgView[i][self.y-1] = crossHairVal
                        imgView[i][self.y+1] = crossHairVal
                for i in range(self.y - 10, self.y + 10):
                    if i >= 0 and i < 192 and self.y > 0 and self.y < 192 and self.x - 1 > 0 and self.x + 1 < 146:
                        imgView[self.x][i] = crossHairVal
                        imgView[self.x-1][i] = crossHairVal
                        imgView[self.x+1][i] = crossHairVal
                self.Data.set(imgView, write = True)
            
            # Setting data for timeplot and horizontal/vertical plots:
            if self.x >= 0 and self.x < 146 and self.y >= 0 and self.y < 192:
                temp = imgRaw
                if self.NoiseColormap.get():
                    temp = self.colormap
                self.PixelData.set(int(temp[self.x][self.y]), write = True)
                if self.PlotHorizontal.get():
                    self.Horizontal.set(temp[self.x], write = True)
                else:
                    self.Horizontal.set(np.zeros(1), write = True)
                if self.PlotVertical.get():
                    self.Vertical.set(temp[:,self.y], write = True)
                else:
                    self.Vertical.set(np.zeros(1), write = True)
                self.Queue.append(imgRaw[self.x][self.y])
                self.ImageQueue.append(imgRaw)

            self.NoiseQueue.append(imgRaw)

            # Histogram generation & automatic contrast processing:
            array = np.array(self.Queue)
            imgArray = np.array(self.ImageQueue)
            mean = imgArray.mean()
            rms = imgArray.std()
            low = np.int32(array.min())
            high = np.int32(array.max())
            binsA = np.arange(low - 10, high + 10, 1)
            histogram, bins = np.histogram(array, bins=binsA)
            bins = np.delete(bins, len(bins) - 1, 0)
            self.Histogram.set(histogram, write = True)
            self.Bins.set(bins, write = True)
            if self.AutoCon.get():
                multiplier = 2
                if self.ApplyDark.get():
                    multiplier = 10
                if self.ShowDark.get():
                    self.MaxPixVal.set(int(self.AvgDark.get().mean() + multiplier * self.AvgDark.get().std()), write = True)
                    self.MinPixVal.set(int(self.AvgDark.get().mean() - multiplier * self.AvgDark.get().std()), write = True)
                else:
                    self.MaxPixVal.set(int(mean + multiplier * rms), write = True)
                    self.MinPixVal.set(int(mean - multiplier * rms), write = True)
                if self.NoiseColormap.get():
                    self.MaxPixVal.set(50, write = True)
                    self.MinPixVal.set(0, write = True)
            self.Updated.set(True, write = True)

class DataReceiverEnvMonitoring(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "StrongBackTemp",
            value = 0,
            description = "Strong back temperature"
        ))
        self.add(pr.LocalVariable(
            name = "AmbientTemp",
            value = 0,
            description = "Ambient temperature"
        ))
        self.add(pr.LocalVariable(
            name = "RelativeHum",
            value = 0,
            description = "Relative humidity"
        ))
        self.add(pr.LocalVariable(
            name = "ASICACurrent",
            value = 0,
            description = "ASIC (A.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "ASICDCurrent",
            value = 0,
            description = "ASIC (D.) current (mA)"
        ))
        self.add(pr.LocalVariable(
            name = "GuardRingCurrent",
            value = 0,
            description = "Guard ring current (uA)"
        ))
        self.add(pr.LocalVariable(
            name = "VccA",
            value = 0,
            description = "Vcc_a (mV)"
        ))
        self.add(pr.LocalVariable(
            name = "VccD",
            value = 0,
            description = "Vcc_d (mV)"
        ))

    def process(self, frame):
        with self.root.updateGroup():
            rawData = bytearray(frame.getPayload())
            frame.read(rawData, 0)
            envData = np.zeros((8,1), dtype='int32')
            for j in range(0,32):
                rawData.pop(0)
            for j in range(0,8):
                envData[j] = int.from_bytes(rawData[j*4:(j+1)*4], byteorder='little')
            envData[0] = envData[0] / 100
            envData[1] = envData[1] / 100
            envData[2] = envData[2] / 100
            self.StrongBackTemp.set(int(envData[0]), write = True)
            self.AmbientTemp.set(int(envData[1]), write = True)
            self.RelativeHum.set(int(envData[2]), write = True)
            self.ASICACurrent.set(int(envData[3]), write = True)
            self.ASICDCurrent.set(int(envData[4]), write = True)
            self.GuardRingCurrent.set(int(envData[5]), write = True)
            self.VccA.set(int(envData[6]), write = True)
            self.VccD.set(int(envData[7]), write = True)
            self.Updated.set(True, write = True)

class DataReceiverPseudoScope(pr.DataReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(pr.LocalVariable(
            name = "ChannelAData",
            value = [],
            description = "Vector data for channel A"
        ))
        self.add(pr.LocalVariable(
            name = "ChannelBData",
            value = [],
            description = "Vector data for channel B"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelAData",
            value = False,
            description = "Whether to show channel A data"
        ))
        self.add(pr.LocalVariable(
            name = "ShowChannelBData",
            value = False,
            description = "Whether to show chanel B data"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXA",
            value = [],
            description = "Vector data for fourier transform x of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYA",
            value = [],
            description = "Vector data for fourier transform y of channel A"
        ))
        self.add(pr.LocalVariable(
            name = "FFTXB",
            value = [],
            description = "Vector data for fourier transform x of channel B"
        ))
        self.add(pr.LocalVariable(
            name = "FFTYB",
            value = [],
            description = "Vector data for fourier transform y of channel B"
        ))

    def process(self, frame):
        rawData = bytearray(frame.getPayload())
        frame.read(rawData,0)
        data  = np.frombuffer(rawData,dtype='uint16')
        data  = data[16:-14]
        oscWords = len(data)
        chAdata = -0.0 + data[0:int(oscWords/2)] * (2.0/2**14)
        chBdata = -0.0 + data[int(oscWords/2): oscWords] * (2.0/2**14)
        chAdata = (2.0-0.053) + chAdata * (-1.04)
        chBdata = (2.0-0.053) + chBdata * (-1.04)
        N = len(chAdata)
        TA = 4E-8
        freqs = []
        yfA = []
        yfB = []
        zeros = np.zeros(1)
        if N > 0:
            freqs = np.fft.rfftfreq(N, TA)
            yfA = np.abs(np.fft.rfft(chAdata))
            yfB = np.abs(np.fft.rfft(chBdata))
            with self.root.updateGroup():
                if self.ShowChannelAData.get():
                    self.ChannelAData.set(chAdata, write = True)
                    self.FFTXA.set(freqs[2:], write = True)
                    self.FFTYA.set(yfA[2:], write = True)
                else:
                    self.ChannelAData.set(zeros, write = True)
                    self.FFTXA.set(zeros, write = True)
                    self.FFTYA.set(zeros, write = True)
                if self.ShowChannelBData.get():
                    self.ChannelBData.set(chBdata, write = True)
                    self.FFTXB.set(freqs[2:], write = True)
                    self.FFTYB.set(yfB[2:], write = True)
                else:
                    self.ChannelBData.set(zeros, write = True)
                    self.FFTXB.set(zeros, write = True)
                    self.FFTYB.set(zeros, write = True)
                self.Updated.set(True, write = True)