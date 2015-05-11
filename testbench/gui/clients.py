#!/usr/bin/env python
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
            'thermals', 'pumps'],
    #
    'all-lights': ['laser', 'lamps'],
    #
    'blurb': ['laser', 'ttl'],
    #

    # lamps
    'lamps': ['QTH', 'XeHg', 'ttl'],

    #-------------------------------------------------------------
    # Thorlabs Laser (4 channels)
    # 
    #
    'laser': { 
        'host': 'lpnlsstbench',
        'commandline': 'laserthorlabs',
        'screen': 'lights',
        'position': {'x': 1950, 'y': 700, 'w': 520, 'h': 420} 
    },
    #-------------------------------------------------------------
    # TTL control (filter wheel, shutters, flipping mirror)
    # 
    #
    'ttl': { 
        'host': 'lpnlsstbench',
        'commandline': 'ttl',
        'screen': 'lights',
        'position': {'x': 1400, 'y': 30, 'w': 490.0, 'h': 300} 
    },

    #-------------------------------------------------------------
    # XYZ mounting
    # 
    'xyz': ['xyz-server', 'xyz-log-console'],
    'xyz-server': { 
        'host': 'lpnlsstbench',
        'commandline': 'xyz-server -....'
    },
    'xyz-log-console': { 
        'host': 'lpnlsstbench',
        'commandline': 'gnome-terminal -x tail -f $HOME/logs/xyz-server.log',
        'screen': 'lights',
        'position': {'x': 1400, 'y': 30, 'w': 490.0, 'h': 300} 
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
        'screen': 'cryo',
        'position': {'x': 96, 'y': 175, 'w': 400.0, 'h': 450} 
    },
    #
    # gnuplot graph!'position': {'x': 96, 'y': 700, 'w': 640.0, 'h': 470} 
    # ...

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
        'screen': 'cryo',
        'position': {'x': 2016, 'y': 175, 'w': 400.0, 'h': 450} 
    }
    #
    # gnuplot graph!


    # agilent pump      2986, 800, 400, 570
    # pfeiffer          3410, 800, 400, 570
    # pressure gnuplot  3170, 175, 640, 470

}
