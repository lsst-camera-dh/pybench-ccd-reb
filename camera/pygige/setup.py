#!/usr/bin/python2.7
import numpy
from distutils.core import setup, Extension
import shutil

module1 = Extension('gige',
          sources = ['PyGige_module.cpp'],
          include_dirs = ['../../../include/', numpy.get_include()],
          library_dirs = ['../../../lib'],
          libraries    = ["gige", "regcli", "pthread", 'cfitsio', "zmq"],
        #define_macros = [("tgt_board_i386", None), ("tgt_os_linux", None)]
)

setup (name = 'pyrce_module',
        version = '1.0',
        description = 'This is a package for VST',
        ext_modules = [module1])
shutil.copy2('build/lib.linux-x86_64-2.7/gige.so', '../')

