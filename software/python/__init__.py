
#!/usr/bin/env python

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
