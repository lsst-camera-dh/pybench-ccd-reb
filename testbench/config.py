#
# LPNHE Testbench for the LSST CCD
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
       # 'host'        : 'lpnlsstacq',
        'driver'      : 'ccd_reb',
        'reb_id'      : 2,
        'stripe'      : 0,
        'xmlfile'     : 'sequencer-soi.xml'
        },
    #
    # ---------------------------------------------------------------------
    # REB (version 2)
    # 
    #
    'wreb': {
      #  'host'        : 'lpnlsstacq',
        'driver'      : 'ccd_reb',
        'reb_id'      : 0xFF,
        'stripe'      : 0,
        'xmlfile'     : 'sequencer-wreb.xml'
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
    # option 1: keithley /dev/ttyS11 8088
    # option 2: no-GUI ultra simple control with keithley-server :
    # keithley-server --device=/dev/ttyS11 --hostname=134.158.155.98 --port=8301
    #
    # 'bss': {
    #     'host'        : 'lpnlsstbench',
    #     'devices'     : ['/dev/ttyS11'],
    #     'driver'      : 'power_backsubstrate',
    #     'port'        : 8088,
    #     'commandline' : 'keithley /dev/ttyS11 8088'
    #     },

    'bss': {
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
        'devices'     : ['/dev/ttyS11'],
        'driver'      : 'power_backsubstrate_ks',
        'port'        : 8301,
        'commandline' : 'keithley-server --device=/dev/ttyS11 --hostname=134.158.155.98 --port=8301'
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
    # oriel /dev/ttyS2 8089
    #
    'QTH': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS2'],
        'driver'      : 'lamp_oriel',
        'port'        : 8089,
        'commandline' : 'oriel %device %port'
        },
    #
    # ---------------------------------------------------------------------
    # XeHg lamp
    # oriel /dev/ttyS3 8085
    #
    'XeHg': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS3'],
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
    # triax /dev/ttyS0 8086 --> not working on June 03 2015
    # triax /dev/ttyS5 
    #
    'triax': {
        'host'        : 'lpnlsstbench',
#SK edit 03062015        'devices'     : ['/dev/ttyS0'],
	'devices'     : ['/dev/ttyS5'],
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
    'lakeshore0': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS7'],
        'driver'      : 'thermal_lakeshore',
        'port'        : 8091,
        'commandline' : 'lakeshore %device %port'
        },
    
    'lakeshore1': {
        'host'        : 'lpnlsstbench',
        'devices'     : ['/dev/ttyS8'],
        'driver'      : 'thermal_lakeshore',
        'port'        : 8091,
        'commandline' : 'lakeshore %device %port'
        },
    # ---------------------------------------------------------------------
    # pressure sensors (Pumps & Pfeiffer)
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
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
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
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
        'devices'     : ['/dev/ttyS1'],
        'driver'      : 'keithley_ks',
        'port'        : 8211,
        'commandline' : 'keithley-server -d'
        },

    # =====================================================================
    #
    # Keithley 6514 multimeter (8211) connected on the DKD photodiode
    # keithley-server -d 
    #
    'DKD' : {
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
        'devices'     : ['/dev/ttyS1'],
        'driver'      : 'keithley_ks',
        'port'        : 8211,
        'commandline' : 'keithley-server -d'
        },

    # =====================================================================
    #
    # Keithley 6514 multimeter (8212) connected on the PhD photodiode
    # keithley-server -d
    #
    'PhD' : {
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
        'devices'     : ['/dev/ttyS13'],
        'driver'      : 'keithley_ks',
        'port'        : 8900,
        'commandline' : 'keithley-server -d'
        },

    # =====================================================================
    #
    # CLAP (from DICE)
    #

    'CLAP' : {
        # 'host'        : 'lpnlsstbench',
        'host'        : '134.158.155.98', ### CRITICAL: put the IP here!
        'devices'     : ['USB'],
        'driver'      : 'sensor_clap',
        'port'        : 8950,
        'commandline' : 'keithley-server -d'
        },


    # =====================================================================
}    

