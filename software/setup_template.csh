# Setup environment
source /afs/slac/g/reseng/rogue/master/setup_env.csh
# source /afs/slac/g/reseng/rogue/v2.2.0/setup_env.csh

# Package directories
setenv SURF_DIR    ${PWD}/../firmware/submodules/surf/python

# Setup python path
setenv PYTHONPATH ${PWD}/python:${SURF_DIR}:${PYTHONPATH}

# set matplotlib to use qt
setenv MPLBACKEND 'Qt4Agg'
