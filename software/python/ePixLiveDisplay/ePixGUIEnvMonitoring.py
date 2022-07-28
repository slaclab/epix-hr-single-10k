#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Configuration file for live environmental monitoring
#-----------------------------------------------------------------------------
# File       : ePixGUIEnvMonitoring.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-07-27
#-----------------------------------------------------------------------------
# Description:
# Configuration file for building the live environmental monitoring GUI using
# PyDM
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

    app = pydm.PyDMApplication(ui_file=ui,
                               command_line_args=args,
                               macros={'dataReceiver': dataReceiver},
                               hide_nav_bar=True,
                               hide_menu_bar=True,
                               hide_status_bar=True)
    app.exec()

class ePixGUIEnvMonitoring(pydm.Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(ePixGUIEnvMonitoring, self).__init__(parent=parent, args=args, macros=macros)
        self.ui.checkBox.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox))
        self.ui.checkBox_2.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_2))
        self.ui.checkBox_3.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_3))
        self.ui.checkBox_4.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_4))
        self.ui.checkBox_5.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_5))
        self.ui.checkBox_6.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_6))
        self.ui.checkBox_7.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_7))
        self.ui.checkBox_8.stateChanged.connect(lambda:self.updateDisplay(self.ui.checkBox_8))
        self.ui.lineEdit.textChanged.connect(self.setTimeSpan)

    def setTimeSpan(self):
        self.ui.PyDMTimePlot.setTimeSpan(int(self.ui.lineEdit.text()))

    def updateDisplay(self, cb):
        if cb.text() == "Strong back temp.":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.StrongBackTemp", name = "Strong back temp.", plot_style = "Line", color = "white", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.StrongBackTemp"))
        if cb.text() == "Ambient temp.":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.AmbientTemp", name = "Ambient temp.", plot_style = "Line", color = "red", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.AmbientTemp"))
        if cb.text() == "Relative Hum.":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.RelativeHum", name = "Relative Hum.", plot_style = "Line", color = "dodgerblue", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.RelativeHum"))
        if cb.text() == "ASIC (A.) current (mA)":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.ASICACurrent", name = "ASIC (A.) current (mA)", plot_style = "Line", color = "forestgreen", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.ASICACurrent"))
        if cb.text() == "ASIC (D.) current (mA)":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.ASICDCurrent", name = "ASIC (D.) current (mA)", plot_style = "Line", color = "yellow", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.ASICDCurrent"))
        if cb.text() == "Guard ring current (uA)":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.GuardRingCurrent", name = "Guard ring current (uA)", plot_style = "Line", color = "magenta", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.GuardRingCurrent"))
        if cb.text() == "Vcc_a (mV)":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.VccA", name = "Vcc_a (mV)", plot_style = "Line", color = "turquoise", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.VccA"))
        if cb.text() == "Vcc_d (mV)":
            if cb.isChecked():
                self.ui.PyDMTimePlot.addYChannel(y_channel = "rogue://0/root.DataReceiverEnvMonitoring.VccD", name = "Vcc_d (mV)", plot_style = "Line", color = "deeppink", lineWidth = 1)
            else:
                self.ui.PyDMTimePlot.removeYChannel(self.ui.PyDMTimePlot.findCurve("rogue://0/root.DataReceiverEnvMonitoring.VccD"))

    def ui_filename(self):
        # Point to the UI file
        return 'ePixViewerEnvPyDM.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.ui_filename())