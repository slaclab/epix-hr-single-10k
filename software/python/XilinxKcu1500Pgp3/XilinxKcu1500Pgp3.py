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
import pyrogue.simulation
import rogue.hardware.data

from DataLib.DataDev import *
from XilinxKcu1500Pgp3.XilinxKcu1500Pgp3Lane import *

class XilinxKcu1500Pgp3(pr.Device):
    def __init__(   self,       
            name        = "XilinxKcu1500Pgp3",
            description = "Container for application registers",
            **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        
        # Add axi-pcie-core 
        self.add(DataDev(            
            offset       = 0x00000000, 
            useBpi       = True,
            expand       = False,
        ))  
        
        # Add PGP Core 
        for i in range(8):
            self.add(XilinxKcu1500Pgp3Lane(            
                name   = ('Lane[%i]' % i), 
                offset = (0x00800000 + i*0x00010000), 
                expand = False,
            ))  
            
        self.add(AxiStreamMonitoring(            
            name        = 'RxLaneMon', 
            offset      = 0x00880000, 
            numberLanes = 8,
            expand      = False,
        )) 
        
        self.add(AxiStreamMonitoring(            
            name        = 'TxLaneMon', 
            offset      = 0x00890000, 
            numberLanes = 8,
            expand      = False,
        ))
