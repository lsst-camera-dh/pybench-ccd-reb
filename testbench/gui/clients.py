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
                # 'background': 'bg-lights-grey.png' },
                'background': 'bg-ccd-grey.png' },
    'cryo':   { 'title': "Cryogeny & Vacuum",
                'desktop': 2,
                'background': 'bg-cryo-grey.png' },
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
                'background': 'bg-default-grey.png' },
    'devel':  { 'title': "Development & Tests",
                'desktop': 6,
                'background': 'bg-default-grey.png' }
}


clients = {
    'all': ['laser', 'lamps', 'ttl',
            'thermals', 'pumps'],
    #
    'all-lights': ['laser', 'ttl', 'QTH', 'XeHg'],
    #
    'blurb': ['laser', 'QTH'],
    #
    'laser': { 'host': 'lpnlsstbench',
               # 'commandline': 'laserthorlabs',
               'commandline': 'xclock -digital',
               'screen': 'lights',
               'position': {'x': 100.0, 'y': 150.0, 'w': 200.0, 'h': 200.0} 
           },
    #
    'QTH':   { 'host': 'lpnlsstbench',
               'commandline': 'xterm -bg blue',
               'screen': 'divers',
               'position': {'x': 500.0, 'y': 150.0, 'w': 200.0, 'h': 200.0} 
           } #,
    # 'xyz': 
    #
}
