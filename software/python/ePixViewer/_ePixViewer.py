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
import ePixViewer.imgProcessing as imgPr
import ePixViewer.Cameras as cameras
import numpy as np
from matplotlib.figure import Figure

import pdb

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


################################################################################
################################################################################
#   Window class
#   Implements the screen that display all images.
#   Calls other classes defined in this file to properly read and process
#   the images in a givel file
################################################################################
class Window(QMainWindow, QObject):
    """Class that defines the main window for the viewer."""
    
    # Define a new signal called 'trigger' that has no arguments.
    imageTrigger = pyqtSignal()
    pseudoScopeTrigger = pyqtSignal()
    monitoringDataTrigger = pyqtSignal()
    processFrameTrigger = pyqtSignal()
    processPseudoScopeFrameTrigger = pyqtSignal()
    processMonitoringFrameTrigger = pyqtSignal()


    def __init__(self, cameraType = 'ePix100a', verbose = False):
        super(Window, self).__init__()    
        self.Verbose = verbose
        # window init
        self.mainWdGeom = [50, 50, 1100, 600] # x, y, width, height
        self.setGeometry(self.mainWdGeom[0], self.mainWdGeom[1], self.mainWdGeom[2],self.mainWdGeom[3])
        self.setWindowTitle("ePix image viewer")

        # creates a camera object
        self.currentCam = cameras.Camera(cameraType = cameraType, verbose=self.Verbose)

        # add actions for menu item
        extractAction = QAction("&Quit", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip('Leave The App')
        extractAction.triggered.connect(self.close_viewer)
        openFile = QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open a new set of images')
        openFile.setStatusTip('Open file')
        openFile.triggered.connect(self.file_open)

        # display status tips for all menu items (or actions)
        self.statusBar()

        # Creates the main menu, 
        mainMenu = self.menuBar()
        # adds items and subitems
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(extractAction)

        # Create widget
        self.prepareWindow()

        # add all buttons to the screen
        self.def_bttns()

        # rogue interconection  #
        # Create the objects            
        self.fileReader  = rogue.utilities.fileio.StreamReader()
        self.eventReader = EventReader(self)
        self.eventReaderScope = EventReader(self)
        self.eventReaderMonitoring = EventReader(self)


        # Connect the fileReader to our event processor
        pyrogue.streamConnect(self.fileReader,self.eventReader)

        # Connect the trigger signal to a slot.
        # the different threads send messages to synchronize their tasks
        self.imageTrigger.connect(self.buildImageFrame)
        self.pseudoScopeTrigger.connect(self.displayPseudoScopeFromReader)
        self.monitoringDataTrigger.connect(self.displayMonitoringDataFromReader) 
        self.processFrameTrigger.connect(self.eventReader._processFrame)
        self.processPseudoScopeFrameTrigger.connect(self.eventReaderScope._processFrame)
        self.processMonitoringFrameTrigger.connect(self.eventReaderMonitoring._processFrame)
        
        # weak way to sync frame reader and display
        self.readFileDelay = 0.1

        # initialize image processing objects
        self.rawImgFrame = []
        self.imgDesc = []
        self.imgTool = imgPr.ImageProcessing(self)

        #init mouse variables
        self.mouseX = 0
        self.mouseY = 0
        self.image = QImage()
        self.pixelTimeSeries = np.array([])

        #initialize data monitoring
        self.monitoringDataTraces = np.zeros((8,1), dtype='int32')
        self.monitoringDataIndex = 0
        self.monitoringDataLength = 100

        #init bit mask
        self.pixelBitMask.setText(str(hex(np.uint16(self.currentCam.bitMask))))


        # display the window on the screen after all items have been added 
        self.show()


    def prepareWindow(self):
        # Center UI
        self.imageScaleMax = int(10000)
        self.imageScaleMin = int(-10000)
        screen = QDesktopWidget().screenGeometry(self)
        size = self.geometry()
        self.buildUi()


    #creates the main display element of the user interface
    def buildUi(self):
        #label used to display image
        self.mainImageDisp = MplCanvas(MyTitle = "Image Display")
        #self.label = QtGui.QLabel()
        #self.label.mousePressEvent = self.mouseClickedOnImage
        self.cid_mousePressEvent = self.mainImageDisp.mpl_connect('button_press_event', self.mouseClickedOnImage)
        #self.label.setAlignment(QtCore.Qt.AlignTop)
        #self.label.setFixedSize(800,800)
        #self.label.setScaledContents(True)
        
        # left hand side layout
        self.mainWidget = QWidget(self)
        vbox1 = QVBoxLayout()
        vbox1.setAlignment(Qt.AlignTop)
        #vbox1.addWidget(self.label,  QtCore.Qt.AlignTop)
        vbox1.addWidget(self.mainImageDisp,  Qt.AlignTop)

        #tabbed control box
        self.gridVbox2 = TabbedCtrlCanvas(self)
        hSubbox1 = QHBoxLayout()
        hSubbox1.addWidget(self.gridVbox2)

        # line plot 1
        self.lineDisplay1 = MplCanvas(MyTitle = "Line Display 1")        
        hSubbox2 = QHBoxLayout()
        hSubbox2.addWidget(self.lineDisplay1)
        
        # line plot 2
        self.lineDisplay2 = MplCanvas(MyTitle = "Line Display 2")        
        hSubbox3 = QHBoxLayout()
        hSubbox3.addWidget(self.lineDisplay2)

        # right hand side layout
        vbox2 = QVBoxLayout()
        vbox2.addLayout(hSubbox1)
        vbox2.addLayout(hSubbox2)
        vbox2.addLayout(hSubbox3)
            
        hbox = QHBoxLayout(self.mainWidget)
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        self.mainWidget.setFocus()        
        self.setCentralWidget(self.mainWidget)


    def setReadDelay(self, delay):
        self.eventReader.readFileDelay = delay
        self.eventReaderScope.readFileDelay = delay
        self.eventReaderMonitoring.readFileDelay = delay
        self.readFileDelay = delay
        

    def file_open(self):
        self.eventReader.frameIndex = 1
        self.eventReader.VIEW_DATA_CHANNEL_ID = 1
        self.setReadDelay(0.1)
        self.filename = QFileDialog.getOpenFileName(self, 'Open File', '', 'Rogue Images (*.dat);; GenDAQ Images (*.bin);;Any (*.*)')  
        if (os.path.splitext(self.filename)[1] == '.dat'): 
            self.displayImagDat(self.filename)
        else:
            self.displayImag(self.filename)


    def def_bttns(self):
        return self
 

    def setPixelBitMask(self):
        #updates the number of images used to calculate the dark image
        try:
            textInput = self.pixelBitMask.text()
            pixelBitMask = int(textInput,16)
            if (pixelBitMask>0):
                self.currentCam.bitMask = pixelBitMask
                print("Pixel Bit Mask Set.")
        except ValueError:
            pixelBitMask = self.currentCam.bitMask
            print("Error: Pixel Bit Mask Not Set. Got: ",self.pixelBitMask.text())        


    def setDark(self):
        #updates the number of images used to calculate the dark image
        try:
            numDarkImg = int(self.numDarkImg.text())
        except ValueError:
            numDarkImg = self.imgTool.numDarkImages
        if (numDarkImg>0):
            self.imgTool.numDarkImages = numDarkImg
        #starts capturing the images for the dark image generation
        self.imgTool.setDarkImg(self.imgDesc)
        print("Dark image requested.")


    def unsetDark(self):
        self.imgTool.unsetDarkImg()
        print("Dark image unset.")
        

    # display the previous frame from the current file
    def prevFrame(self):
        self.eventReader.frameIndex = int(self.frameNumberLine.text()) - 1
        if (self.eventReader.frameIndex<1):
            self.eventReader.frameIndex = 1
        self.frameNumberLine.setText(str(self.eventReader.frameIndex))
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)


    # display the next frame from the current file
    def nextFrame(self):
        self.eventReader.frameIndex = int(self.frameNumberLine.text()) + 1
        self.frameNumberLine.setText(str(self.eventReader.frameIndex))
        print('Selected frame ', self.eventReader.frameIndex)
        self.displayImagDat(self.filename)


    # checks if the user really wants to exit
    def close_viewer(self):
        choice = QMessageBox.question(self, 'Quit!',
                                            "Do you want to quit viewer?",
                                            QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            print("Exiting now...")
            #sys.exit()
            self.hide()
        else:
            pass


    # if the image is png or other standard extension it uses this function to display it.
    def displayImag(self, path):
        print('File name: ', path)
        if path:
            image = QImage(path)
            self.mainImageDisp.update_figure(image)
#            pp = QtGui.QPixmap.fromImage(image)
#            self.label.setPixmap(pp.scaled(
#                    self.label.size(),
#                    QtCore.Qt.KeepAspectRatio,
#                    QtCore.Qt.SmoothTransformation))


    # if the image is a rogue type, calls the file reader object to read all frames
    def displayImagDat(self, filename):

        print('File name: ', filename)
        self.eventReader.readDataDone = False
        self.eventReader.numAcceptedFrames = 0
        self.fileReader.open(filename)

        # waits until data is found
        timeoutCnt = 0
        while ((self.eventReader.readDataDone == False) and (timeoutCnt < 10)):
             timeoutCnt += 1
             print('Loading image...', self.eventReader.frameIndex, 'atempt',  timeoutCnt)
             time.sleep(0.1)
    
    # build image frame. 
    # If image frame is completed calls displayImageFromReader
    # If image is incomplete stores the partial image
    def buildImageFrame(self):
        newRawData = self.eventReader.frameData
        [frameComplete, readyForDisplay, self.rawImgFrame] = self.currentCam.buildImageFrame(currentRawData = self.rawImgFrame, newRawData = newRawData)

        if (readyForDisplay):
            self.displayImageFromReader(imageData = self.rawImgFrame)
            
        if (frameComplete == 0 and readyForDisplay == 1):
        # in this condition we have data about two different images
        # since a new image has been sent and the old one is incomplete
        # the next line preserves the new data to be used with the next frame
            self.rawImgFrame = newRawData
        if (frameComplete == 1):
        # frees the memory since it has been used alreay enabling a new frame logic to start fresh
            self.rawImgFrame = []              
        

    # core code for displaying the image
    def displayImageFromReader(self, imageData):
        #init variables
        self.imgTool.imgWidth = self.currentCam.sensorWidth
        self.imgTool.imgHeight = self.currentCam.sensorHeight
        #get descrambled image com camera
        self.imgDesc = self.currentCam.descrambleImage(imageData)
                    
        arrayLen = len(self.imgDesc)

        self._updateImageScales()

        if (self.imgTool.imgDark_isSet):
            self.ImgDarkSub = self.imgTool.getDarkSubtractedImg(self.imgDesc)
            _8bitImg = self.ImgDarkSub#self.imgTool.reScaleImgTo8bit(self.ImgDarkSub, self.imageScaleMax, self.imageScaleMin)
        else:
            # get the data into the image object
            _8bitImg = self.imgDesc#self.imgTool.reScaleImgTo8bit(self.imgDesc, self.imageScaleMax, self.imageScaleMin)

        #self.image = QtGui.QImage(_8bitImg.repeat(4), self.imgTool.imgWidth, self.imgTool.imgHeight, QtGui.QImage.Format_RGB32)
        
        #pp = QtGui.QPixmap.fromImage(self.image)
        if self.imageScaleMax > self.imageScaleMin:
            self.mainImageDisp.update_figure(_8bitImg, contrast=[self.imageScaleMax, self.imageScaleMin], autoScale = False)
        else:
            self.mainImageDisp.update_figure(_8bitImg, contrast=[self.imageScaleMin, self.imageScaleMax], autoScale = False)
        #self.label.setPixmap(pp.scaled(self.label.size(),QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation))
        #self.label.adjustSize()
        # updates the frame number
        # this sleep is a weak way of waiting for the file to be readout completely... needs improvement
        time.sleep(self.readFileDelay)
        thisString = 'Frame {} of {}'.format(self.eventReader.frameIndex, self.eventReader.numAcceptedFrames)

        self.postImageDisplayProcessing()        


    """Checks the value on the user interface, if valid update them"""
    def _updateImageScales(self):
        #saves current values locally
        imageScaleMax = self.imageScaleMax
        imageScaleMin = self.imageScaleMin
        try:
            self.imageScaleMax = int(self.imageScaleMaxLine.text())
            self.imageScaleMin = int(self.imageScaleMinLine.text())
        except ValueError:
            self.imageScaleMax = imageScaleMax
            self.imageScaleMin = imageScaleMin
            
        
    def displayPseudoScopeFromReader(self):
        # saves data locally
        rawData = self.eventReaderScope.frameDataScope
        # converts bytes to array of dwords
        data  = np.frombuffer(rawData,dtype='uint16')
        # limits trace length for fast display (may be removed in the future)

        #header are 8 32 bit words
        #footer are 5 32 bit words
        data  = data[16:-14]
        oscWords = len(data)

        chAdata = -0.0 + data[0:int(oscWords/2)] * (2.0/2**14)
        chBdata = -0.0 + data[int(oscWords/2): oscWords] * (2.0/2**14)

        #TODO: add radio button to make the inversion selectable.
        invertPolarityChA = True
        invertPolarityChB = True

        if invertPolarityChA == True :
            chAdata = (2.0-0.053) + chAdata * (-1.04)

        if invertPolarityChB == True :
            chBdata = (2.0-0.053) + chBdata * (-1.04)

        print("avgValueChA", str(np.mean(chAdata)))
        
        if (self.LinePlot2_RB1.isChecked()):
            self.lineDisplay2.update_plot(self.cbScopeCh0.isChecked(), "Scope Trace A", 'r',  chAdata, 
                                            self.cbScopeCh1.isChecked(), "Scope Trace B", 'b',  chBdata)
       

    def displayMonitoringDataFromReader(self):
        rawData = self.eventReaderMonitoring.frameDataMonitoring
        envData = np.zeros((8,1), dtype='int32')
        
        #exits if there is no 
        if (len(rawData)==0) :        
            return false
        #removes header before displying the image
        for j in range(0,32):
            rawData.pop(0)
        for j in range(0,8):
            envData[j] = int.from_bytes(rawData[j*4:(j+1)*4], byteorder='little')
        #convert temperature and humidity by spliting for 100
        envData[0] = envData[0]  / 100 
        envData[1] = envData[1]  / 100 
        envData[2] = envData[2]  / 100 

        if (self.monitoringDataIndex == 0):
            self.monitoringDataTraces = envData
        else:
            self.monitoringDataTraces = np.append(self.monitoringDataTraces, envData, 1)
        
        if (self.LinePlot2_RB2.isChecked()):
            self.lineDisplay2.update_plot(self.cbEnvMonCh0.isChecked(), "Env. Data 0", 'r',  self.monitoringDataTraces[0,:], 
                                            self.cbEnvMonCh1.isChecked(), "Env. Data 1", 'b',  self.monitoringDataTraces[1,:],
                                            self.cbEnvMonCh2.isChecked(), "Env. Data 2", 'g',  self.monitoringDataTraces[2,:],
                                            self.cbEnvMonCh3.isChecked(), "Env. Data 3", 'y',  self.monitoringDataTraces[3,:],
                                            self.cbEnvMonCh4.isChecked(), "Env. Data 4", 'r+-', self.monitoringDataTraces[4,:], 
                                            self.cbEnvMonCh5.isChecked(), "Env. Data 5", 'b+-', self.monitoringDataTraces[5,:],
                                            self.cbEnvMonCh6.isChecked(), "Env. Data 6", 'g+-', self.monitoringDataTraces[6,:],
                                            self.cbEnvMonCh7.isChecked(), "Env. Data 7", 'y+-', self.monitoringDataTraces[7,:])

        #increments position
        self.monitoringDataIndex = self.monitoringDataIndex + 1  
        if (self.monitoringDataIndex > self.monitoringDataLength):
            self.monitoringDataTraces = np.delete(self.monitoringDataTraces, 0, 1)


    # Evaluates which post display algorithms are needed if any
    def postImageDisplayProcessing(self):
        #saves dark image set, if requested
        if (self.imgTool.imgDark_isRequested):
            self.imgTool.setDarkImg(self.imgDesc)
        #if the image gets done, saves it for other processes
        if (self.imgTool.imgDark_isSet):
            self.ImgDarkSub = self.imgTool.getDarkSubtractedImg(self.imgDesc)
            
        #check horizontal line display
        if ((self.cbHorizontalLineEnabled.isChecked()) or (self.cbVerticalLineEnabled.isChecked()) or (self.cbpixelTimeSeriesEnabled.isChecked())):
            self.updatePixelTimeSeriesLinePlot()
            self.updateLinePlots()
    
    def updateLinePlots(self):
        ##if (PRINT_VERBOSE): print('Horizontal plot processing')
   
        #full line plot
        if (self.imgTool.imgDark_isSet):
            #self.ImgDarkSub        
            self.lineDisplay1.update_plot(self.cbHorizontalLineEnabled.isChecked(),  "Horizontal", 'r', self.ImgDarkSub[self.mouseY,:], 
                                            self.cbVerticalLineEnabled.isChecked(),    "Vertical",   'b', self.ImgDarkSub[:,self.mouseX],
                                            self.cbpixelTimeSeriesEnabled.isChecked(), "Pixel TS",   'k', self.pixelTimeSeries)
        else:
            #self.imgDesc
            self.lineDisplay1.update_plot(self.cbHorizontalLineEnabled.isChecked(),  "Horizontal", 'r', self.imgDesc[self.mouseY,:], 
                                            self.cbVerticalLineEnabled.isChecked(),    "Vertical",   'b', self.imgDesc[:,self.mouseX],
                                            self.cbpixelTimeSeriesEnabled.isChecked(), "Pixel TS",   'k', self.pixelTimeSeries)


    """ Plot pixel values for multiple images """
    def clearPixelTimeSeriesLinePlot(self):
        self.pixelTimeSeries = np.array([])


    def updatePixelTimeSeriesLinePlot(self):
        ##if (PRINT_VERBOSE): print('Horizontal plot processing')
   
        #full line plot
        try:
            if (self.imgTool.imgDark_isSet):
                self.pixelTimeSeries = np.append(self.pixelTimeSeries, self.ImgDarkSub[self.mouseY,self.mouseX])
            else:
                self.pixelTimeSeries = np.append(self.pixelTimeSeries, self.imgDesc[self.mouseY,self.mouseX])

            if(not self.cbpixelTimeSeriesEnabled.isChecked()):
                self. clearPixelTimeSeriesLinePlot()
        except:
            print ("Error at updatePixelTimeSeriesLinePlot().\n")

    """Save the enabled series to file"""
    def SaveSeriesToFile(self):
        #open a pop up menu to set the filename
        self.filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'csv file (*.csv);; Any (*.*)')
        if (self.cbHorizontalLineEnabled.isChecked()):
            if (self.imgTool.imgDark_isSet):
                np.savetxt(os.path.splitext(self.filename)[0] + "_horizontal" + os.path.splitext(self.filename)[1], self.ImgDarkSub[self.mouseY,:], fmt='%d', delimiter=',', newline='\n')
            else:
                np.savetxt(os.path.splitext(self.filename)[0] + "_horizontal" + os.path.splitext(self.filename)[1], self.imgDesc[self.mouseY,:], fmt='%d', delimiter=',', newline='\n')                    

        if (self.cbVerticalLineEnabled.isChecked()):
            if (self.imgTool.imgDark_isSet):
                np.savetxt(os.path.splitext(self.filename)[0] + "_vertical" + os.path.splitext(self.filename)[1], self.ImgDarkSub[:,self.mouseX], fmt='%d', delimiter=',', newline='\n')
            else:
                np.savetxt(os.path.splitext(self.filename)[0] + "_vertical" + os.path.splitext(self.filename)[1], self.imgDesc[:,self.mouseX], fmt='%d', delimiter=',', newline='\n')                    

        if (self.cbpixelTimeSeriesEnabled.isChecked()):
            np.savetxt(os.path.splitext(self.filename)[0] + "_pixel" + os.path.splitext(self.filename)[1], self.pixelTimeSeries, fmt='%d', delimiter=',', newline='\n')
        
        
    def _paintEvent(self, e):
        qp = QPainter()
        qp.begin(self.image) 
        self.drawCross(qp)
        qp.end()

    def drawPoint(self, qp):
        qp.setPen(Qt.red)
        size = self.label.size()
        imageH = self.image.height()
        imageW = self.image.width()
        pixmapH = self.label.height()
        pixmapW = self.label.width()

        if ((self.mouseX > 0)and(self.mouseX<imageW)):
            if ((self.mouseY > 0)and(self.mouseY < imageH)):
                x = int(self.mouseX * pixmapW / imageW)
                y = int(self.mouseY * pixmapH / imageH)
                qp.drawPoint(x , y)

    def drawCross(self, qp):
        qp.setPen(Qt.red)
        size = self.label.size()
        imageH = self.image.height()
        imageW = self.image.width()
        pixmapH = self.label.height()
        pixmapW = self.label.width()

        if ((self.mouseX > 0)and(self.mouseX<imageW)):
            if ((self.mouseY > 0)and(self.mouseY < imageH)):
                x = int(self.mouseX * pixmapW / imageW)
                y = int(self.mouseY * pixmapH / imageH)
                qp.drawLine(x-2 , y-2, x+2 , y+2)
                qp.drawLine(x-2 , y+2, x+2 , y-2)

    def mouseClickedOnImage(self, event):
        if (self.imgDesc != []):
            #mouseX = event.pos().x()
            #mouseY = event.pos().y()
            self.mouseX, self.mouseY = int(event.xdata), int(event.ydata)
            #pixmapH = self.label.height()
            #pixmapW = self.label.width()
            #imageH = self.image.height()
            #imageW = self.image.width()
    
            #self.mouseX = int(imageW*mouseX/pixmapW)
            #self.mouseY = int(imageH*mouseY/pixmapH)
            
            if (self.imgTool.imgDark_isSet):
                self.mousePixelValue = self.ImgDarkSub[self.mouseY, self.mouseX]
            elif (self.imgDesc != []):
                self.mousePixelValue = self.imgDesc[self.mouseY, self.mouseX]

            # clear the pixel time sereis every time the pixel of interest is changed
            self.clearPixelTimeSeriesLinePlot()
    
            #print('Raw mouse coordinates: {},{}'.format(mouseX, mouseY))
            #print('Pixel map dimensions: {},{}'.format(pixmapW, pixmapH))
            #print('Image dimensions: {},{}'.format(imageW, imageH))
            print('Pixel[{},{}] = {}'.format(self.mouseX, self.mouseY, self.mousePixelValue))
            self.mouseXLine.setText(str(self.mouseX))
            self.mouseYLine.setText(str(self.mouseY))
            self.mouseValueLine.setText(str(self.mousePixelValue))
            #test on update_figure
            self.updateLinePlots()
            if (self.cbImageZoomEnabled.isChecked()):
                if (self.imgTool.imgDark_isSet):
                    self.lineDisplay1.update_figure(self.ImgDarkSub[self.mouseY-10:self.mouseY+10, self.mouseX-10:self.mouseX+10],contrast=[self.imageScaleMax, self.imageScaleMin], autoScale = False)
                elif (self.imgDesc != []):
                    self.lineDisplay1.update_figure(self.imgDesc[self.mouseY-10:self.mouseY+10, self.mouseX-10:self.mouseX+10],contrast=[self.imageScaleMax, self.imageScaleMin], autoScale = False)
            


################################################################################
################################################################################
#   Event reader class
#   
################################################################################
class EventReader(rogue.interfaces.stream.Slave):
    """retrieves data from a file using rogue utilities services"""

    def __init__(self, parent) :
        rogue.interfaces.stream.Slave.__init__(self)
        super(EventReader, self).__init__()
        self.enable = True
        self.numAcceptedFrames = 0
        self.numProcessFrames  = 0
        self.numSkipFrames = 1 # 1 accpts all frames, 2 accepts every other frame, 3 every thrid frame and so on
        self.lastFrame = rogue.interfaces.stream.Frame
        self.frameIndex = 1
        self.frameData = bytearray()
        self.frameDataArray = [bytearray(),bytearray(),bytearray(),bytearray()] # bytearray()
        self.frameDataScope = bytearray()
        self.frameDataMonitoring = bytearray()
        self.readDataDone = False
        self.parent = parent
        self.lastTime = time.clock_gettime(0)
        self.Verbose = parent.Verbose
        self.isLCLSII = False
        
        #############################
        # define the data type IDs
        #############################
        self.VIEW_DATA_CHANNEL_ID    = 0x1
        self.VIEW_PSEUDOSCOPE_ID     = 0x2
        self.VIEW_MONITORING_DATA_ID = 0x3
        self.readFileDelay = 0.1
        

    def setDataDisplayParameters(self, timingType, displayNum):
        # timing type
        # 0 for no timing uses generic PCIe firmware
        # 1 LCLS timing
        # 2 for LCLS-II timing
        if timingType == 0:
            #############################
            # define the data type IDs
            #############################
            self.isLCLSII = False
            self.VIEW_DATA_CHANNEL_ID    = 0x0
            self.VIEW_PSEUDOSCOPE_ID     = 0x2
            self.VIEW_MONITORING_DATA_ID = 0x3
        elif timingType == 1:
            #############################
            # define the data type IDs
            #############################
            self.isLCLSII = False
            self.VIEW_DATA_CHANNEL_ID    = 0x1
            self.VIEW_PSEUDOSCOPE_ID     = 0x2
            self.VIEW_MONITORING_DATA_ID = 0x3
        elif timingType == 2:
            #############################
            # define the data type IDs
            #############################
            self.isLCLSII = True
            self.VIEW_DATA_CHANNEL_ID    = 0x3 + displayNum
            self.VIEW_PSEUDOSCOPE_ID     = -1
            self.VIEW_MONITORING_DATA_ID = -1
        else:
            #############################
            # define the data type IDs
            #############################
            self.isLCLSII = False
            self.VIEW_DATA_CHANNEL_ID    = 0x1
            self.VIEW_PSEUDOSCOPE_ID     = 0x2
            self.VIEW_MONITORING_DATA_ID = 0x3

        print(f'Parameters, LCLS timing, DATA VC')
        print(self.isLCLSII, self.VIEW_DATA_CHANNEL_ID)
    # Checks all frames in the file to look for the one that needs to be displayed
    # self.frameIndex defines which frame should be returned.
    # Once the frame is found, saves data and emits a signal do enable the class window
    # to dislplay it. The emit signal is needed because only that class' thread can 
    # access the screen.
    def _acceptFrame(self,frame):
        channel = frame.getChannel()
        #print("Channel: ", channel)
        ## enter debug mode
        #print("\n---------------------------------\n-\n- Entering DEBUG mode _acceptFrame \n-\n-\n--------------------------------- ")
        #pdb.set_trace()
        if (not self.parent.isHidden() and (channel>1 or self.isLCLSII==False)):
            self.lastFrame = frame
            # reads entire frame
            p = bytearray(self.lastFrame.getPayload())
            self.lastFrame.read(p,0)
            if (self.Verbose): print('_accepted p[',self.numAcceptedFrames, ']: ', p[0:10])
            if (self.Verbose): print('Length of accpeted frame: ' , len(p)) 
            self.frameDataArray[self.numAcceptedFrames%4][:] = p#bytearray(self.lastFrame.getPayload())
            self.numAcceptedFrames += 1
            if (self.isLCLSII==True):
                VcNum = channel
                if (self.Verbose): print("LCLSII VcNum: ", VcNum)
                if (self.Verbose): print("Viewer ID: ", self.VIEW_DATA_CHANNEL_ID)
            else:
                VcNum =  p[0] & 0xF
                if (self.Verbose): print("VcNum: ", VcNum)

            if (time.clock_gettime(0)-self.lastTime)>1:
                if ((VcNum == self.VIEW_PSEUDOSCOPE_ID)):
                    self.lastTime = time.clock_gettime(0)
                    if (self.Verbose): print('Decoding PseudoScopeData')
                    self.parent.processPseudoScopeFrameTrigger.emit()
                elif (VcNum == self.VIEW_MONITORING_DATA_ID):
                    self.lastTime = time.clock_gettime(0)
                    if (self.Verbose): print('Decoding Monitoring Data')
                    self.parent.processMonitoringFrameTrigger.emit()
                elif (VcNum == self.VIEW_DATA_CHANNEL_ID):
                    self.lastTime = time.clock_gettime(0)
                    if (self.Verbose): print('Decoding ASIC Data')
                    if (((self.numAcceptedFrames == self.frameIndex) or (self.frameIndex == 0)) and (self.numAcceptedFrames%self.numSkipFrames==0)): 
                        self.parent.processFrameTrigger.emit()


    def _processFrame(self):

        index = self.numProcessFrames%4
        self.numProcessFrames += 1
        if (self.enable):        
            # Get the channel number
            chNum = (self.lastFrame.getFlags() >> 24)
            # reads payload only
            p = self.frameDataArray[index] 
            # reads entire frame
            VcNum =  p[0] & 0xF
            if (self.Verbose): print('-------- Frame ',self.numAcceptedFrames,'Channel flags',self.lastFrame.getFlags() , ' Channel Num:' , chNum, ' Vc Num:' , VcNum)
            # Check if channel number is 0x1 (streaming data channel)
            if (chNum == self.VIEW_DATA_CHANNEL_ID or VcNum == 0) :
                # Collect the data
                if (self.Verbose): print('-------- Frame ',self.numAcceptedFrames,'Channel flags',self.lastFrame.getFlags() , ' Channel Num:' , chNum, ' Vc Num:' , VcNum)
                if (self.Verbose): print('Num. image data readout: ', len(p))
                self.frameData = p
                cnt = 0
#                if ((self.numAcceptedFrames == self.frameIndex) or (self.frameIndex == 0)):              
                self.readDataDone = True
                # Emit the signal.
                self.parent.imageTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without 
                # freezing or crashing the program. 
#                time.sleep(self.readFileDelay)
            
            #during stream chNumId is not assigned so these ifs cannot be used to distiguish the frames
            #during stream VIEW_PSEUDOSCOPE_ID is set to zero
            if (chNum == self.VIEW_PSEUDOSCOPE_ID or VcNum == self.VIEW_PSEUDOSCOPE_ID) :
                #view Pseudo Scope Data
                if (self.Verbose): print('Num. pseudo scope data readout: ', len(p))
                self.frameDataScope[:] = p
                # Emit the signal.
                self.parent.pseudoScopeTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without 
                # freezing or crashing the program. 
#                time.sleep(self.readFileDelay)

            if (chNum == self.VIEW_MONITORING_DATA_ID or VcNum == self.VIEW_MONITORING_DATA_ID) :
                #view Pseudo Scope Data
                if (self.Verbose): print('Num. slow monitoring data readout: ', len(p))
                self.frameDataMonitoring[:] = p
                # Emit the signal.
                self.parent.monitoringDataTrigger.emit()
                # if displaying all images the sleep produces a frame rate that can be displayed without 
                # freezing or crashing the program. 
#                time.sleep(self.readFileDelay)



################################################################################
################################################################################
#   Matplotlib class
#   
################################################################################
class MplCanvas(FigureCanvas):
    """This is a QWidget derived from FigureCanvasAgg."""


    def __init__(self, parent=None, width=5, height=4, dpi=100, MyTitle=""):

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.MyTitle = MyTitle
        self.axes.set_title(self.MyTitle)
        self.fig.cbar = None

        

    def compute_initial_figure(self):
        #if one wants to plot something at the begining of the application fill this function.
        #self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'b')
        self.axes.plot([], [], 'b')

    def update_plot(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [-1, -2, 10, 14] #[random.randint(0, 10) for i in range(4)]
        #self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()

    #the arguments are expected in the following sequence
    # (display enabled, line name, line color, data array)
    def update_plot(self, *args):
        argIndex = 0
        lineName = ""
#        if (self.fig.cbar!=None):              
#            self.fig.cbar.remove()

        self.axes.cla()
        for arg in args:
            if (argIndex == 0):
                lineEnabled = arg
            if (argIndex == 1):
                lineName = arg
            if (argIndex == 2):
                lineColor = arg
            if (argIndex == 3):
                ##if (PRINT_VERBOSE): print(lineName)
                if (lineEnabled):
                    l = arg #[random.randint(0, 10) for i in range(4)]
                    #self.axes.set_ylim((-0.1,2.1))
                    #self.axes.set_xticks(np.arange(0, len(l), 20))
                    #self.axes.set_yticks(np.arange(0, 2., 0.25))
                    self.axes.plot(l, lineColor)
                    self.axes.grid()
                argIndex = -1
            argIndex = argIndex + 1    
        self.axes.set_title(self.MyTitle)        
        self.draw()

    def update_figure(self, image=None, contrast=None, autoScale = True):
        self.axes.cla()
        self.axes.autoscale = autoScale

        if (len(image)>0):
            #self.axes.gray()        
            if (contrast != None):
                self.cax = self.axes.imshow(image, interpolation='nearest', cmap='gray',vmin=contrast[1], vmax=contrast[0])
            else:
                self.cax = self.axes.imshow(image, interpolation='nearest', cmap='gray')

#            if (self.fig.cbar==None):              
#                self.fig.cbar = self.fig.colorbar(self.cax)
#            else:
#                self.fig.cbar.remove()
#                self.fig.cbar = self.fig.colorbar(self.cax)
        self.draw()

        


################################################################################
################################################################################
#   Tabbed control class
#   
################################################################################
class TabbedCtrlCanvas(QTabWidget):
    #https://pythonspot.com/qt4-tabs/ tips on tabs
    def __init__(self, parent):
        super(TabbedCtrlCanvas, self).__init__()

        # pointer to the parent class
        myParent = parent

        # Create tabs
        tab1	= QWidget()	
        tab2	= QWidget()
        tab3    = QWidget()
        tab4    = QWidget()

        ######################################################      
        # create widgets for tab 1 (Main)
        ######################################################
        # label used to display frame number
        self.labelFrameNum = QLabel('')
        # button set dark
        btnSetDark = QPushButton("Set Dark")
        btnSetDark.setMaximumWidth(150)
        btnSetDark.clicked.connect(myParent.setDark)
        btnSetDark.resize(btnSetDark.minimumSizeHint())
        # button unset dark
        btnUnSetDark = QPushButton("Unset Dark")
        btnUnSetDark.setMaximumWidth(150)
        btnUnSetDark.clicked.connect(myParent.unsetDark)
        btnUnSetDark.resize(btnUnSetDark.minimumSizeHint())    
        numDarkImgLabel = QLabel("Number of Dark images")
        myParent.numDarkImg = QLineEdit()
        myParent.numDarkImg.setMaximumWidth(150)
        myParent.numDarkImg.setMinimumWidth(100)
        myParent.numDarkImg.setText(str(10))
        # button quit
        btnQuit = QPushButton("Quit")
        btnQuit.setMaximumWidth(150)
        btnQuit.clicked.connect(myParent.close_viewer)
        btnQuit.resize(btnQuit.minimumSizeHint())
        # mouse buttons
        mouseLabel = QLabel("Pixel Information")
        myParent.mouseXLine = QLineEdit()
        myParent.mouseXLine.setMaximumWidth(150)
        myParent.mouseXLine.setMinimumWidth(100)
        myParent.mouseYLine = QLineEdit()
        myParent.mouseYLine.setMaximumWidth(150)
        myParent.mouseYLine.setMinimumWidth(100)
        myParent.mouseValueLine = QLineEdit()
        myParent.mouseValueLine.setMaximumWidth(150)
        myParent.mouseValueLine.setMinimumWidth(100)
        # set bitmask
        btnSetPixelBitMask = QPushButton("Set")
        btnSetPixelBitMask.setMaximumWidth(150)
        btnSetPixelBitMask.clicked.connect(myParent.setPixelBitMask)
        btnSetPixelBitMask.resize(btnSetPixelBitMask.minimumSizeHint())    
        pixelBitMaskLabel = QLabel("Pixel Bit Mask")
        myParent.pixelBitMask = QLineEdit()
        myParent.pixelBitMask.setMaximumWidth(150)
        myParent.pixelBitMask.setMinimumWidth(100)
        myParent.pixelBitMask.setInputMask("0xHHHH")
        # label contrast
        imageScaleLabel = QLabel("Contrast (max, min)")
        myParent.imageScaleMaxLine = QLineEdit()
        myParent.imageScaleMaxLine.setMaximumWidth(100)
        myParent.imageScaleMaxLine.setMinimumWidth(50)
        myParent.imageScaleMaxLine.setText(str(myParent.imageScaleMax))
        myParent.imageScaleMinLine = QLineEdit()
        myParent.imageScaleMinLine.setMaximumWidth(100)
        myParent.imageScaleMinLine.setMinimumWidth(50)
        myParent.imageScaleMinLine.setText(str(myParent.imageScaleMin))
        
        # set layout to tab 1
        tab1Frame = QFrame()
        tab1Frame.setFrameStyle(QFrame.Panel);
        tab1Frame.setGeometry(100, 200, 0, 0)
        tab1Frame.setLineWidth(1);
        grid = QGridLayout()
        grid.setSpacing(5)
        grid.addWidget(tab1Frame,0,0,7,7)

        # add widgets to tab1
        grid.addWidget(numDarkImgLabel, 1, 1)
        grid.addWidget(myParent.numDarkImg, 1, 2)
        grid.addWidget(btnSetDark, 1, 3)
        grid.addWidget(btnUnSetDark, 1, 4)
        grid.addWidget(mouseLabel, 2, 1)
        grid.addWidget(myParent.mouseXLine, 2, 2)
        grid.addWidget(myParent.mouseYLine, 2, 3)
        grid.addWidget(myParent.mouseValueLine, 2, 4)
        grid.addWidget(pixelBitMaskLabel, 3, 1)
        grid.addWidget(myParent.pixelBitMask, 3, 2)
        grid.addWidget(btnSetPixelBitMask, 3, 3)
        grid.addWidget(imageScaleLabel, 4, 1)
        grid.addWidget(myParent.imageScaleMaxLine, 4, 2)
        grid.addWidget(myParent.imageScaleMinLine,4, 3)     

        # complete tab1
        tab1.setLayout(grid)

        ######################################################      
        # create widgets for tab 2 (File controls)
        ######################################################      
        # button prev
        btnPrevFrame = QPushButton("Prev")
        btnPrevFrame.setMaximumWidth(150)
        btnPrevFrame.clicked.connect(myParent.prevFrame)
        btnPrevFrame.resize(btnPrevFrame.minimumSizeHint())

        # button next
        btnNextFrame = QPushButton("Next")
        btnNextFrame.setMaximumWidth(150)
        btnNextFrame.clicked.connect(myParent.nextFrame)
        btnNextFrame.resize(btnNextFrame.minimumSizeHint())    

        # frame number
        myParent.frameNumberLine = QLineEdit()
        myParent.frameNumberLine.setMaximumWidth(100)
        myParent.frameNumberLine.setMinimumWidth(50)
        myParent.frameNumberLine.setText(str(1))

        # set layout to tab 2
        tab2Frame1 = QFrame()
        tab2Frame1.setFrameStyle(QFrame.Panel);
        tab2Frame1.setGeometry(100, 200, 0, 0)
        tab2Frame1.setLineWidth(1);
        
        # add widgets into tab2
        grid2 = QGridLayout()
        grid2.setSpacing(5)
        grid2.setColumnMinimumWidth(0, 1)
        grid2.setColumnMinimumWidth(2, 1)
        grid2.setColumnMinimumWidth(3, 1)
        grid2.setColumnMinimumWidth(5, 1)
        grid2.addWidget(tab2Frame1,0,0,5,7)
        grid2.addWidget(btnNextFrame, 1, 1)
        grid2.addWidget(btnPrevFrame, 1, 2)
        grid2.addWidget(myParent.frameNumberLine, 2, 1)

        # complete tab2
        tab2.setLayout(grid2)

        
        ######################################################      
        # create widgets for tab 3 (Line Display 1)
        ######################################################      

        # check boxes
        myParent.cbHorizontalLineEnabled = QCheckBox('Plot Horizontal Line')
        #
        myParent.cbVerticalLineEnabled = QCheckBox('Plot Vertical Line')
        #
        myParent.cbpixelTimeSeriesEnabled = QCheckBox('Pixel Time Series Line')
        myParent.cbImageZoomEnabled = QCheckBox('Image zoom')

        # button save trace to file
        btnSaveSeriesToFile = QPushButton("Save to file")
        btnSaveSeriesToFile.setMaximumWidth(150)
        btnSaveSeriesToFile.clicked.connect(myParent.SaveSeriesToFile)
        btnSaveSeriesToFile.resize(btnSaveSeriesToFile.minimumSizeHint())    


        # set layout to tab 3
        tab3Frame1 = QFrame()
        tab3Frame1.setFrameStyle(QFrame.Panel);
        tab3Frame1.setGeometry(100, 200, 0, 0)
        tab3Frame1.setLineWidth(1);
        
        # add widgets into tab2
        grid3 = QGridLayout()
        grid3.setSpacing(5)
        grid3.setColumnMinimumWidth(0, 1)
        grid3.setColumnMinimumWidth(2, 1)
        grid3.setColumnMinimumWidth(3, 1)
        grid3.setColumnMinimumWidth(5, 1)
        grid3.addWidget(tab3Frame1,0,0,5,7)
        grid3.addWidget(myParent.cbHorizontalLineEnabled,1, 1)
        grid3.addWidget(myParent.cbVerticalLineEnabled,2, 1)
        grid3.addWidget(myParent.cbpixelTimeSeriesEnabled,3, 1)
        grid3.addWidget(myParent.cbImageZoomEnabled,1, 3)
        grid3.addWidget(btnSaveSeriesToFile,4, 1)


        # complete tab3
        tab3.setLayout(grid3)
 
        ######################################################      
        # create widgets for tab 4 (Line display 2)
        ######################################################      

        # radio buttons
        # http://www.tutorialspoint.com/pyqt/pyqt_qradiobutton_widget.htm
        myParent.LinePlot2_RB1 = QRadioButton("Scope")
        myParent.LinePlot2_RB1.setChecked(True)
        myParent.LinePlot2_RB2 = QRadioButton("Env. Monitoring")

        # check boxes
        myParent.cbScopeCh0 = QCheckBox('Channel 0')
        myParent.cbScopeCh1 = QCheckBox('Channel 1')
        #        
        myParent.cbEnvMonCh0 = QCheckBox('Strong back temp.')
        myParent.cbEnvMonCh1 = QCheckBox('Ambient temp.')
        myParent.cbEnvMonCh2 = QCheckBox('Relative Hum.')
        myParent.cbEnvMonCh3 = QCheckBox('ASIC (A.) current (mA)')
        myParent.cbEnvMonCh4 = QCheckBox('ASIC (D.) current (mA)')
        myParent.cbEnvMonCh5 = QCheckBox('Guard ring current (uA)')
        myParent.cbEnvMonCh6 = QCheckBox('Vcc_a (mV)')
        myParent.cbEnvMonCh7 = QCheckBox('Vcc_d (mV)')


        # set layout to tab 3
        tab4Frame1 = QFrame()
        tab4Frame1.setFrameStyle(QFrame.Panel);
        tab4Frame1.setGeometry(100, 200, 0, 0)
        tab4Frame1.setLineWidth(1);
        
        # add widgets into tab2
        grid4 = QGridLayout()
        grid4.setSpacing(5)
        grid4.setColumnMinimumWidth(0, 1)
        grid4.setColumnMinimumWidth(2, 1)
        grid4.setColumnMinimumWidth(3, 1)
        grid4.setColumnMinimumWidth(5, 1)
        grid4.addWidget(tab4Frame1,0,0,7,7)
        grid4.addWidget(myParent.LinePlot2_RB1, 1, 1)
        grid4.addWidget(myParent.cbScopeCh0, 2, 1)
        grid4.addWidget(myParent.cbScopeCh1, 3, 1)  
        grid4.addWidget(myParent.LinePlot2_RB2, 1, 3)
        grid4.addWidget(myParent.cbEnvMonCh0, 2, 3)
        grid4.addWidget(myParent.cbEnvMonCh1, 3, 3)  
        grid4.addWidget(myParent.cbEnvMonCh2, 4, 3)  
        grid4.addWidget(myParent.cbEnvMonCh3, 5, 3)  
        grid4.addWidget(myParent.cbEnvMonCh4, 2, 4)  
        grid4.addWidget(myParent.cbEnvMonCh5, 3, 4)  
        grid4.addWidget(myParent.cbEnvMonCh6, 4, 4)  
        grid4.addWidget(myParent.cbEnvMonCh7, 5, 4)  

        # complete tab4
        tab4.setLayout(grid4)


        # Add tabs
        self.addTab(tab1,"Main")
        self.addTab(tab2,"File controls")
        self.addTab(tab3,"Line Display 1")
        self.addTab(tab4,"Line Display 2")

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('')    
        self.show()


