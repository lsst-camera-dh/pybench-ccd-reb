# -*- mode: python -*- 


APPNAME  = 'lsst'
VERSION  = '0.0.1'
top   = '.'
out   = 'build'

description = "LSST Camera Test Bench module"
requirements = []



def options(opt):
    opt.load('compiler_cc')
    opt.load('python') 
    # opt.load('compiler_cxx')

    # opt.load('qt4')
    
def configure(ctx):
    ctx.load('compiler_cc')
    ctx.load('python')
    # ctx.load('compiler_cxx')
    # ctx.load('qt4')
    # ctx.load('slow_qt4')
    ctx.check_python_headers()
    # ctx.env['CCFLAGS'] = ['-fPIC', '-DPIC']
    
    # ctx.check_cc(lib='rt')
    # ctx.check_cc(lib='ftd2xx', 
    #               uselib_store = 'FTDI2xx',
    #               libpath=ctx.env.PREFIX + '/lib')


    # ctx.check_cc(lib='rt')

    # # ------ libftd2xx.so.0.4.16
    # ctx.check_cc(lib = 'ftd2xx', 
    #               uselib_store = 'FTDI2xx',
    #               libpath = ctx.env.PREFIX + '/lib')
 

def build(ctx):    
    ctx(features = 'py', 
        # source = bld.path.ant_glob('*.py'), 
        source = ['__init__.py'], 
        install_path = '${PYTHONDIR}/lsst')

    ctx.recurse(['camera', 'testbench'])
    


