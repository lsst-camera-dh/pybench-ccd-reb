1#!/usr/bin/env python
#
# Startup script for the LSST CCD testbench at LPNHE
# Configuration of all the clients
#

screens = {
    'ccd':    { 'title': "Master Console",
                'desktop': 0,
                'background': 'bg-ccd-grey.png' },
    'lights': { 'title': "Light Sources",
                'desktop': 1,
                'background': 'bg-light-sources.png' },
    'cryos':   { 'title': "Cryogeny & Vacuum",
                'desktop': 2,
                'background': 'bg-cryo-pumps.png' },
    'logs':   { 'title': "Logs",
                'desktop': 3,
                'background': 'bg-ccd-grey.png' },
                # 'background': 'bg-logs-grey.png' },
    'divers': { 'title': "divers",
                'desktop': 4,
                'background': 'bg-ccd-grey.png' },
                # 'background': 'bg-default-grey.png' },
    'www':    { 'title': "www",
                'desktop': 5,
                'background': 'bg-ccd-grey.png' },
    'devel':  { 'title': "Development & Tests",
                'desktop': 6,
                'background': 'bg-ccd-grey.png' }
}


clients = {
    'all': ['laser', 'lamps', 'ttl',
            'thermals', 'pumps', 'xyz'],
    #
    'all-lights': ['laser', 'lamps'],
    #
    'blurb': ['laser', 'ttl'],
    #

    # lamps
    'lamps': ['QTH', 'XeHg', 'ttl'],

    #-------------------------------------------------------------
    # Lamp Oriel QTH
    # 
    #
    'QTH': { 
        'host': 'lpnlsstbench',
        'commandline': 'oriel /dev/ttyS2 8089',
        'screen': 'lights',
        'position': {'x': 2200, 'y': 700, 'w': 400, 'h': 300} 
    },
    #-------------------------------------------------------------
    # Lamp Oriel XeHg
    # 
    #
    'XeHg': { 
        'host': 'lpnlsstbench',
        'commandline': 'oriel /dev/ttyS3 8085',
        'screen': 'lights',
        'position': {'x': 3160, 'y': 700, 'w': 400, 'h': 300} 
    },
    #-------------------------------------------------------------
    # Thorlabs Laser (4 channels)
    # 
    #
    'laser': { 
        'host': 'lpnlsstbench',
        'commandline': 'laserthorlabs',
        'screen': 'lights',
        'position': {'x': 1480, 'y': 700, 'w': 400, 'h': 420} 
    },
    #-------------------------------------------------------------
    # TTL control (filter wheel, shutters, flipping mirror)
    # 
    #
    'ttl': { 
        'host': 'lpnlsstbench',
        'commandline': 'ttl',
        'screen': 'lights',
        'position': {'x': 1950, 'y': 30, 'w': 490, 'h': 300} 
    },

    #-------------------------------------------------------------
    # Monochromator Triax 180
    # 
    #
    'triax': { 
        'host': 'lpnlsstbench',
        'commandline': 'triax',
        'screen': 'lights',
        'position': {'x': 3070, 'y': 30, 'w': 490, 'h': 300} 
    },

    #-------------------------------------------------------------
    # XYZ mounting
    # 
    'xyz': ['xyz-server', 'xyz-log'],
    'xyz-server': { 
        'host': 'lpnlsstbench',
        'commandline': 'xyz-server -d'
    },
    'xyz-log': { 
        'host': 'lpnlsstbench',
        'commandline': 'xterm -title "XYZ(A)" -fa Monospace -fs 10 -e tail -f /home/lsst/logs/xyz-server.log',
        'screen': 'lights',
        'position': {'x': 74, 'y': 830, 'w': 800, 'h': 260} 
    },
    #-------------------------------------------------------------
    # Cryo & Pumps Cryostat chamber #0 (blue)
    #
    'cryo0': ['cryo-0'], # alias
    'cryo-0': ['cryogeny-0', 'pump-0'],
    # 
    'cryogeny-0': ['lakeshore-0', 'cryo-0-temp-graph'],
    #
    'lakeshore-0': { 
        'host': 'lpnlsstbench',
        'commandline': 'lakeshore',
        'screen': 'cryos',
        'position': {'x': 96, 'y': 175, 'w': 400.0, 'h': 450} 
    },
    #
    # gnuplot graph!'position': {'x': 96, 'y': 700, 'w': 640.0, 'h': 470} 
    # ...

    'pump-0': ['agilent-pump-0', 'pfeiffer-0', 'cryo-0-pressure-graph'],
    # agilent pump      1066, 800, 400, 570
    # pfeiffer          1490, 800, 400, 570
    # pressure gnuplot  1250, 175, 640, 470

    #-------------------------------------------------------------
    # Cryo & Pumps Cryostat chamber #1 (red)
    # 
    'cryo1': ['cryo-1'], # alias
    'cryo-1': ['cryogeny-1', 'pump-1'],
    #
    'cryogeny-1': ['lakeshore-1', 'cryo-1-temp-graph'],
    #
    'lakeshore-1': { 
        'host': 'lpnlsstbench',
        'commandline': 'lakeshore',
        'screen': 'cryos',
        'position': {'x': 2016, 'y': 175, 'w': 400.0, 'h': 450} 
    },
    #,
    # gnuplot graph!

    'pump-1': ['agilent-pump-1', 'pfeiffer-1', 'cryo-1-pressure-graph']

    # agilent pump      2986, 800, 400, 570
    # pfeiffer          3410, 800, 400, 570
    # pressure gnuplot  3170, 175, 640, 470
    #-------------------------------------------------------------
    # General Bench log
    
    # 'bench-log' ...

    # 'bss-log' : 

    #-------------------------------------------------------------

}
