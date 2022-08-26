#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Configuration file for live image viewer
#-----------------------------------------------------------------------------
# File       : ePixGUI.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-08-26
#-----------------------------------------------------------------------------
# Description:
# Configuration file for building the live image viewer GUI using PyDM
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import os
import pydm

def runEpixDisplay(dataReceiver, serverList='localhost:9090', root=None,
    title=None,sizeX=800,sizeY=1000,maxListExpand=5,maxListSize=100):

    #pyrogue.pydm.runPyDM()

    if root is not None:

        if not root.running:
            raise Exception("Attempt to use pydm with root that has not started")

        os.environ['ROGUE_SERVERS'] = 'localhost:{}'.format(root.serverPort)
    else:
        os.environ['ROGUE_SERVERS'] = serverList

    ui = os.path.abspath(__file__)

    if title is None:
        title = "Epix Live Display: {}".format(os.getenv('ROGUE_SERVERS'))

    args = []
    args.append(f"sizeX={sizeX}")
    args.append(f"sizeY={sizeY}")
    args.append(f"title='{title}'")
    args.append(f"maxListExpand={maxListExpand}")
    args.append(f"maxListSize={maxListSize}")

    macrosA = {}
    macrosA['dataReceiver'] = dataReceiver
    app = pydm.PyDMApplication(ui_file=ui,
                               command_line_args=args,
                               macros=macrosA,
                               hide_nav_bar=True,
                               hide_menu_bar=True,
                               hide_status_bar=True)
    app.exec()

class ePixGUI(pydm.Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        print(f'{macros=}')
        self._dataReceiver = macros['dataReceiver']
        self.ui.PyDMImageView.newImageSignal.connect(self.updateDisplay)
        self.ui.PyDMImageView.scene.sigMouseClicked.connect(self.clickProcess)
        # self.ui.PyDMLineEdit_3.textChanged.connect(self.resetTimePlot)
        # self.ui.PyDMLineEdit_6.textChanged.connect(self.resetTimePlot)
        # self.ui.lineEdit.textChanged.connect(self.setTimeSpan)
        # self.ui.PyDMCheckbox_15.stateChanged.connect(self.resetTimePlot)
        # self.ui.pushButton.clicked.connect(self.resetTimePlot)

    def updateDisplay(self):
        maxContrast = int(self.ui.PyDMLineEdit_5.displayText())
        minContrast = int(self.ui.PyDMLineEdit_4.displayText())
        self.ui.PyDMImageView.setColorMapLimits(minContrast, maxContrast)

    # def setTimeSpan(self):
    #     self.ui.PyDMTimePlot.setTimeSpan(int(self.ui.lineEdit.text()))

    def clickProcess(self, event):
        pos = self.ui.PyDMImageView.getView().getViewBox().mapSceneToView(event.scenePos())
        x = str(int(pos.x()))
        y = str(int(pos.y()))
        self.ui.PyDMLineEdit_2.setText(x)
        self.ui.PyDMLineEdit_2.send_value()
        self.ui.PyDMLineEdit_6.setText(y)
        self.ui.PyDMLineEdit_6.send_value()

    # def resetTimePlot(self):
    #     self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve(
    #         f'{self._dataReceiver}.PixelData'))
    #     self.ui.PyDMTimePlot.addYChannel(
    #         y_channel = f'{self._dataReceiver}.PixelData', 
    #         name = "Pixel counts", 
    #         plot_style = "Line", 
    #         color = "white", 
    #         lineWidth = 1)

    def ui_filename(self):
        # Point to the UI file
        return 'ePixViewerPyDM.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.ui_filename())