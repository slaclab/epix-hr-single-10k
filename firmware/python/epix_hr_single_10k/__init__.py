#-----------------------------------------------------------------------------
# This file is part of the 'epix-hr-single-10k'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'epix-hr-single-10k', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

# this sys.path.append is a hack to allow a rogue device to import its
# own version of device-specific submodules (surf/axi-pcie-core etc.) that
# have been placed as subdirectories here by setup.py.  ryan herbst
# thinks of these packages as a device-specific "board support package".
# this allows one to put multiple devices in the same conda env.
# a cleaner approach would be to use relative imports everywhere, but
# that would be a lot of work for the tid-air people - cpo.
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
