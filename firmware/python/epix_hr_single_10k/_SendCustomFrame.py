#-----------------------------------------------------------------------------
# This file is part of the 'ePix HR Camera Firmware'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'ePix HR Camera Firmware', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import rogue.interfaces.stream
import numpy as np
import click
import pyrogue
import struct

class SendCustomFrame(rogue.interfaces.stream.Master, rogue.interfaces.stream.Slave):

    def __init__(self):
        rogue.interfaces.stream.Slave.__init__(self)
        rogue.interfaces.stream.Master.__init__(self)

        # 28x28x4byte (32-bit input data interface)
        self.ibSize = 384*384*2

        # 145x384x8byte (16-bit output data interface) 445,440
        self.obSize = 145*384*8 

        self.testImage = np.ones((145,384),dtype=np.uint64)*12
        self.testImage[100,:] = 0
        self._width = 384
        self._height = 145
        self._fullData = []


    def SendCustomFrame(self):
        # Here we request a frame capable of holding `self.ibSize` bytes
        frame = self._reqFrame(self.obSize, True)

        # Fill the frame with the test image
        for i in range(self._height):
            for j in range(self._width):
                ba = bytearray(struct.pack("<H", self.testImage[i,j] ))
                #ba = self.testImage[i,j]
                frame.write(ba,2*(i*self._width+j))
                #frame.write(ba, (i*self._width+j))

        # Send the frame
        print( f'ibFrame.getPayload() = {frame.getPayload()}' )
        self._sendFrame(frame)

    def SendCalibFrame(self):
        # Here we request a frame capable of holding `self.ibSize` bytes
        frame = self._reqFrame(self.obSize, True)

        # Fill the frame with the test image
        for i in range(self._height):
            for j in range(self._width):
                ba = bytearray(struct.pack("<Q", self.testImage[i,j] ))
                #ba = self.testImage[i,j]
                frame.write(ba,8*(i*self._width+j))
                #frame.write(ba, (i*self._width+j))

        # Send the frame
        print( f'ibFrame.getPayload() = {frame.getPayload()}' )
        self._sendFrame(frame)

    # Method which is called when a frame is received
    def _acceptFrame(self,frame):

        # First it is good practice to hold a lock on the frame data.
        with frame.lock():

            # Next we can get the size of the frame payload
            size = frame.getPayload()
            print( f'obFrame.getPayload() = {size}' )

            #ba = bytearray(4)
            #for i in range(32):
            #    frame.read(ba,4*i)
            #    print(ba)
            #    result = struct.unpack('<I', ba)
            #    result = ba
            #    print( f'Destination array:   {result[0]}' )

            fullData = bytearray(size)
            frame.read(fullData,0)
            self._fullData = fullData
            #print(fullData)

    def __eq__(self,other):
        pyrogue.streamConnectBiDir(other,self)
