from setuptools import setup

# use softlinks to make the various "board-support-package" submodules
# look like subpackages.  Then __init__.py will modify
# sys.path so that the correct "local" versions of surf etc. are
# picked up.  A better approach would be using relative imports
# in the submodules, but that's more work.  -cpo
setup(
    name = 'epix_hr_single_10k',
    description = 'Epix HR package',
    packages = [
        'epix_hr_single_10k',
        'epix_hr_single_10k.ePixAsics',
        'epix_hr_single_10k.ePixFpga',
        'epix_hr_single_10k.ePixViewer',
        'epix_hr_single_10k.XilinxKcu1500Pgp3',
        'epix_hr_single_10k.surf',
        'epix_hr_single_10k.surf.devices',
        'epix_hr_single_10k.surf.devices.analog_devices',
        'epix_hr_single_10k.surf.devices.cypress',
        'epix_hr_single_10k.surf.devices.intel',
        'epix_hr_single_10k.surf.devices.linear',
        'epix_hr_single_10k.surf.devices.microchip',
        'epix_hr_single_10k.surf.devices.micron',
        'epix_hr_single_10k.surf.devices.nxp',
        'epix_hr_single_10k.surf.devices.silabs',
        'epix_hr_single_10k.surf.devices.ti',
        'epix_hr_single_10k.surf.devices.transceivers',
        'epix_hr_single_10k.surf.ethernet',
        'epix_hr_single_10k.surf.ethernet.gige',
        'epix_hr_single_10k.surf.ethernet.mac',
        'epix_hr_single_10k.surf.ethernet.ten_gig',
        'epix_hr_single_10k.surf.ethernet.udp',
        'epix_hr_single_10k.surf.ethernet.xaui',
        'epix_hr_single_10k.surf.misc',
        'epix_hr_single_10k.surf.protocols',
        'epix_hr_single_10k.surf.protocols.batcher',
        'epix_hr_single_10k.surf.protocols.clink',
        'epix_hr_single_10k.surf.protocols.i2c',
        'epix_hr_single_10k.surf.protocols.jesd204b',
        'epix_hr_single_10k.surf.protocols.pgp',
        'epix_hr_single_10k.surf.protocols.rssi',
        'epix_hr_single_10k.surf.protocols.ssi',
        'epix_hr_single_10k.surf.xilinx',
    ],
    package_dir = {
        'epix_hr_single_10k': 'software/python',
        'epix_hr_single_10k.surf': 'firmware/submodules/surf/python/surf',
        'epix_hr_single_10k.axi-pcie-core': 'firmware/submodules/axi-pcie-core/python/axipcie',
        'epix_hr_single_10k.ePixAsics': 'software/python/ePixAsics',
        'epix_hr_single_10k.ePixFpga': 'software/python/ePixFpga',
        'epix_hr_single_10k.ePixViewer': 'software/python/ePixViewer',
        'epix_hr_single_10k.XilinxKcu1500Pgp3': 'software/python/XilinxKcu1500Pgp3',
    }
)
