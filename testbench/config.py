#
# baseline configuration of instrument drivers: devices and XML-RPC ports
# This file is used by all the Testbench scripts.
#
# Authors: L. Le Guillou, E. Sepulveda
#
config = {
    # =====================================================================
    #  Dummy drivers (tests only)
    # =====================================================================

    'dummy': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/null'],
        'driver'      : 'dummy_dummy',
        'port'        : 8666,
        'commandline' : '/bin/false'
        },

    'wallace': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/null'],
        'driver'      : 'wallace_gromit',
        'port'        : 8999,
        'commandline' : '/bin/false'
        },

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
        'host'        : 'lpnlsstacq',
        # 'devices'     : ['/dev/laser'],
        'driver'      : 'ccd_reb',
        'reb_id'      : 2
        # 'port'        : 8082,
        # 'commandline' : 'laserthorlabs'
        },
    #
    # ---------------------------------------------------------------------
    # REB (version 2)
    # 
    #
    'reb2': {
        'host'        : 'lpnlsstacq',
        # 'devices'     : ['/dev/laser'],
        'driver'      : 'ccd_reb2',
        'reb_id'      : 2
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
    # 'bss': {
    #     'host'        : 'lpnlsstbench',
    #     'devices'     : ['/dev/ttyS11'],
    #     'driver'      : 'power_backsubstrate',
    #     'port'        : 8088,
    #     'commandline' : 'keithley /dev/ttyS11 8088'
    #     },

    'bss': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS11'],
        'driver'      : 'power_backsubstrate_ks',
        'port'        : 8301,
        'commandline' : 'keithley-server --device=/dev/ttyS11 --hostname=lpnlsstbench --port=8301'
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
        'host'        : 'lpnlsstbench',
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
        'host'        : 'lpnlsstbench',
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
        'host'        : 'lpnlsstbench',
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
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyUSB0'],
        'driver'      : 'monochromator_triax',
        'port'        : 8086,
        'commandline' : 'triax %device %port'
        },
    #
    # ---------------------------------------------------------------------
    # Newport monochromator
    # ...
    # ...
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
        'host'        : 'lpnlsstbench',
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
    # XYZ pollux (8201) /dev/ttyS16, /dev/ttyS17, /dev/ttyS18
    # xyz-server -d
    #
    'xyz' : {
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98',
        'devices'     : ['/dev/ttyS16', '/dev/ttyS17', '/dev/ttyS18'],
        'driver'      : 'xyz_pollux',
        'port'        : 8201,
        'commandline' : 'xyz-server -d'
        },


    #
    # =====================================================================
    #  Multimeters / Photodiodes
    # =====================================================================
    #
    # Keithley 6514 multimeter (8211)
    # keithley-server -d
    #
    'keithley' : {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS1'],
        'driver'      : 'keithley_ks',
        'port'        : 8211,
        'commandline' : 'keithley-server -d'
        }

    # =====================================================================
}    

