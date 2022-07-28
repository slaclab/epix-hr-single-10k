#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : Configuration file for live pseudoscope monitoring
#-----------------------------------------------------------------------------
# File       : ePixGUIPseudoScope.py
# Author     : Jaeyoung (Daniel) Lee
# Created    : 2022-06-22
# Last update: 2022-07-27
#-----------------------------------------------------------------------------
# Description:
# Configuration file for building the live pseudoscope monitoring GUI using
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

class ePixGUIPseudoScope(pydm.Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(ePixGUIPseudoScope, self).__init__(parent=parent, args=args, macros=macros)

    def ui_filename(self):
        # Point to the UI file
        return 'ePixViewerPseudoPyDM.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), self.ui_filename())