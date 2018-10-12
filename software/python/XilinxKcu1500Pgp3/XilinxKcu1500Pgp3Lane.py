#!/usr/bin/env python
##############################################################################
## This file is part of 'camera-link-gen1'.
## It is subject to the license terms in the LICENSE.txt file found in the 
## top-level directory of this distribution and at: 
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
## No part of 'camera-link-gen1', including this file, 
## may be copied, modified, propagated, or distributed except according to 
## the terms contained in the LICENSE.txt file.
##############################################################################

import pyrogue as pr
import pyrogue.interfaces.simulation
#import pyrogue.simulation
#import rogue.hardware.data

from DataLib.DataDev import *
from surf.protocols.pgp._Pgp3AxiL import *
from surf.axi._AxiStreamMonitoring    import *

class XilinxKcu1500Pgp3Lane(pr.Device):
    def __init__(   self,       
            name        = "XilinxKcu1500Pgp3Lane",
            description = "Container for application registers",
            **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        
        self.add(pr.RemoteVariable( 
            name         = "RxVcBlowoff",
            description  = "RxVcBlowoff",
            offset       = 0x000,
            bitSize      = 16,
            bitOffset    = 0,
            base         = pr.UInt,
            mode         = "RW",
        ))   

        self.add(AxiStreamMonitoring(            
            name        = 'RxVcMon', 
            offset      = 0x1000, 
            numberLanes = 16,
            expand      = False,
        )) 
        
        self.add(AxiStreamMonitoring(            
            name        = 'TxVcMon', 
            offset      = 0x2000, 
            numberLanes = 16,
            expand      = False,
        ))
        
        self.add(Pgp3AxiL(            
            offset  = 0x8000, 
            numVc   = 16, # 16 VC per lane
            writeEn = True,
            expand  = False,
        ))  

        
