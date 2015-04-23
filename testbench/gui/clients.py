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
                'background': '/tmp/bg-light-sources.png' },
    'cryo':   { 'title': "Cryogeny & Vacuum",
                'desktop': 2,
                'background': '/tmp/bg-cryo-pumps.png' },
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
    'blurb': ['laser', 'ttl'],
    #
    'laser': { 'host': 'lpnlsstbench',
               'commandline': 'laserthorlabs',
               'screen': 'lights',
               'position': {'x': 1950, 'y': 750, 'w': 420, 'h': 420} 
           },
    #
    'ttl':   { 'host': 'lpnlsstbench',
               'commandline': 'ttl',
               'screen': 'divers',
               'position': {'x': 1400, 'y': 30, 'w': 490.0, 'h': 300} 
           } #,
    # 'xyz': 
    #
}
