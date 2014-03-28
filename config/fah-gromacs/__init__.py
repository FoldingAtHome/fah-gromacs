from SCons.Script import *
import sys


def configure_deps(conf):
    env = conf.env

    conf.CBCheckHome('fah-gromacs', inc_suffix = '', lib_suffix = '')

    # Libraries
    for lib in ['nsl', 'm', 'pthread', 'gsl']:
        if conf.CBCheckLib(lib):
            env.CBDefine('HAVE_LIB' + lib.upper())


    # MKL
    if conf.CBConfig('mkl', False) and conf.CBCheckCHeader('mkl_dfti.h'):
        env.CBDefine('GMX_FFT_MKL')


    # XDR
    if not conf.CBCheckCHeader('rpc/xdr.h'): env.CBDefine('GMX_INTERNAL_XDR')


    # libxml2
    try:
        env.ParseConfig('xml2-config --libs --cflags')
    except: pass # Ignore errors
    if conf.CBCheckLib('xml2') and conf.CBCheckCHeader('libxml/parser.h'):
        env.CBDefine('HAVE_LIBXML2')


    env.CBDefine('GMX_DOUBLE')


def configure(conf):
    env = conf.env

    found = False

    # This is missing from some libxml2 deps
    env.PrependUnique(LIBS = ['z'])

    # Try to use pkg-config
    if not int(env.get('fah', 0)):
        try:
            env.ParseConfig('pkg-config --libs --cflags libgmx_d libmd_d')
            found = True
        except: pass

    # Else try manual configuration
    if not found: conf.CBConfig('fah-gromacs-deps')

    # Check for Gromacs libraries
    for lib in ['gmx', 'md']:
        if int(env.get('fah', 0)): conf.CBRequireLib(lib + '-fah')
        elif not conf.CBCheckLib(lib + '_d'): conf.CBRequireLib(lib)

    # Check for Gromacs header
    conf.CBRequireCHeader('gromacs/tpxio.h')

    env.CBDefine('HAVE_GROMACS')


def generate(env):
    env.CBAddConfigTest('fah-gromacs', configure)
    env.CBAddConfigTest('fah-gromacs-deps', configure_deps)
    env.CBLoadTools('mkl')
    env.CBAddVariables(
        BoolVariable('fah', 'Set to 1 to build for Folding@home', 0))


def exists(env):
    return 1
