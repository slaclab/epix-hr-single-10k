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
import axipcie as pcie
import surf.protocols.pgp as pgp

class XilinxKcu1500Pgp3(pr.Device):
    def __init__(   self,       
            name        = "XilinxKcu1500Pgp3",
            description = "Container for application registers",
            **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        
        # Add axi-pcie-core 
        self.add(pcie.AxiPcieCore(          
            offset = 0x00000000, 
            expand = False,
        ))  
        
        # Add PGP Core 
        for i in range(8):
            self.add(pgp.Pgp3AxiL(            
                name    = ('Lane[%i]' % i), 
                offset  = (0x00800000 + i*0x00010000), 
                numVc   = 4, # 4 VC per lane
                writeEn = True,
                expand  = False,
            ))             
