# Setup environment
#source /afs/slac/g/reseng/rogue/master/setup_env.csh
source /afs/slac/g/reseng/rogue/v2.12.0/setup_env.csh
#source /afs/slac/g/reseng/rogue/v2.9.1/setup_env.csh
#source /afs/slac/g/reseng/rogue/pre-release/setup_env.csh

# Package directories
setenv SURF_DIR    ${PWD}/../firmware/submodules/surf/python
setenv PCIE_DIR    ${PWD}/../firmware/submodules/axi-pcie-core/python

# Setup python path
setenv PYTHONPATH ${PWD}/python:${SURF_DIR}:${PCIE_DIR}:${PYTHONPATH}

# set matplotlib to use qt
setenv MPLBACKEND 'Qt4Agg'
