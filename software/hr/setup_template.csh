
# Python 3 support
source /afs/slac.stanford.edu/g/reseng/python/3.6.1/settings.csh
source /afs/slac.stanford.edu/g/reseng/boost/1.64.0/settings.csh

# Python 2 support
#source /afs/slac.stanford.edu/g/reseng/python/2.7.13/settings.csh
#source /afs/slac.stanford.edu/g/reseng/boost/1.62.0_p2/settings.csh

source /afs/slac.stanford.edu/g/reseng/zeromq/4.2.1/settings.csh
source /afs/slac.stanford.edu/g/reseng/epics/base-R3-16-0/settings.csh

# Package directories
setenv 	EPIXROGUE_DIR    ${PWD}
#setenv SURF_DIR   ${PWD}/../surf
setenv SURF_DIR   ${PWD}/../../firmware/submodules/surf
setenv ROGUE_DIR  ${PWD}/../rogue
#setenv ROGUE_DIR  /afs/slac/g/reseng/rogue/v1.2.3

# Setup python path
setenv PYTHONPATH ${PWD}/python:${SURF_DIR}/python:${ROGUE_DIR}/python:${PYTHONPATH}

# Setup library path
setenv LD_LIBRARY_PATH ${ROGUE_DIR}/python::${LD_LIBRARY_PATH}


# Boot thread library names differ from system to system, not all have -mt
setenv BOOST_THREAD -lboost_thread-mt

# set matplotlib to use qt
setenv MPLBACKEND 'Qt4Agg'
