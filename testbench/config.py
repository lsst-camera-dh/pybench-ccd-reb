#
# baseline configuration of instrument drivers: devices and XML-RPC ports
# This file is used by all the Testbench scripts.
#
# Authors: L. Le Guillou, E. Sepulveda
#
config = {
    # =====================================================================
    #  CCD Controllers
    # =====================================================================
    #
    #
    # ---------------------------------------------------------------------
    # REB (version 1)
    # 
    #
    'reb': {
        'host'        : 'lpnws4122',
        # 'devices'     : ['/dev/laser'],
        'driver'      : 'ccd_reb' #,
        # 'port'        : 8082,
        # 'commandline' : 'laserthorlabs'
        },
    #
    # ---------------------------------------------------------------------
    # REB (version 2)
    # 
    #
    'reb2': {
        'host'        : 'lpnws4122',
        # 'devices'     : ['/dev/laser'],
        'driver'      : 'ccd_reb2' #,
        # 'port'        : 8082,
        # 'commandline' : 'laserthorlabs'
        },
    # ---------------------------------------------------------------------
    # C-REB (???)
    #
    # ...
    # =====================================================================
    #  Power supplys
    # =====================================================================
    #
    # ---------------------------------------------------------------------
    # Agilent power supply
    # *critical*
    #
    #
    # ---------------------------------------------------------------------
    # Keithley 6487 current+voltage source
    # *Critical*
    # backsubstrate bias power supply
    # option 1: keithley /dev/ttyUSB4 8088
    # option 2: no-GUI ultra simple control with keithley-server
    #
    'bss': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB4'],
        'driver'      : 'power_backsubstrate',
        'port'        : 8088,
        'commandline' : 'keithley /dev/ttyUSB4 8088'
        },
    #
    # ---------------------------------------------------------------------
    #


    # ---------------------------------------------------------------------

    #
    # =====================================================================
    #  Light sources
    # =====================================================================
    #
    # ---------------------------------------------------------------------
    # Laser Thorlabs (8082)
    # laserthorlabs
    #
    'laser': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/laser'],
        'driver'      : 'laser_thorlabs',
        'port'        : 8082,
        'commandline' : 'laserthorlabs'
        },
    #
    # ---------------------------------------------------------------------
    # QTH lamp
    # oriel /dev/ttyUSB3 8089
    #
    'QTH': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB3'],
        'driver'      : 'lamp_oriel',
        'port'        : 8089,
        'commandline' : 'oriel %device %port'
        },
    #
    # ---------------------------------------------------------------------
    # XeHg lamp
    # oriel /dev/ttyUSB2 8085
    #
    'XeHg': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB2'],
        'driver'      : 'lamp_oriel',
        'port'        : 8085,
        'commandline' : 'oriel %device %port'
        },
    #
    # =====================================================================
    #  Monochromator(s)
    # =====================================================================
    #
    # ---------------------------------------------------------------------
    # Triax monochromator
    # triax /dev/ttyUSB0 8086
    #
    'triax': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB0'],
        'driver'      : 'monochromator_triax',
        'port'        : 8086,
        'commandline' : 'triax %device %port'
        },
    #
    # ---------------------------------------------------------------------
    # Newport monochromator
    # ...
    #
    # ---------------------------------------------------------------------

    # =====================================================================
    #  TTL interface (National Instruments)
    # =====================================================================
    #
    # ---------------------------------------------------------------------
    # TTL interface National Instrument PCI board (8083)
    # ttl
    #
    'ttl': {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/comedi0'],
        'driver'      : 'ttl_ni',
        'port'        : 8083,
        'commandline' : 'ttl'
        },
    #
    # ---------------------------------------------------------------------
    #
    # =====================================================================
    #  Cryostat temperature and pressure control
    # =====================================================================
    #
    # ---------------------------------------------------------------------
    # Lakeshore (TODO: there will be several Lakeshores !)
    #
    # temperature
    # ---------------------------------------------------------------------
    # pressure sensors
    #
    #
    # =====================================================================
    #  Optical bench motors
    # =====================================================================
    #
    # XYZ pollux (8101) /dev/ttyUSB8, /dev/ttyUSB9, /dev/ttyUSB10
    # xyz-server -d
    #
    'xyz' : {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB8', '/dev/ttyUSB9', '/dev/ttyUSB10'],
        'driver'      : 'xyz_pollux',
        'port'        : 8101,
        'commandline' : 'xyz-server -d'
        }


    #
    # =====================================================================
    #  Multimeters / Photodiodes
    # =====================================================================
    #
    # Keithley 6514 multimeter (8102)
    # keithley-server -d
    #
    'keithley' : {
        'host'        : 'lpnlsst',
        'devices'     : ['/dev/ttyUSB1'],
        'driver'      : 'keithley',
        'port'        : 8102,
        'commandline' : 'keithley-server -d'
        }

    # =====================================================================
}    

