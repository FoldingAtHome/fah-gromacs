# Setup
import os
env = Environment()
try:
    env.Tool('config', toolpath = [os.environ.get('CBANG_HOME')])
except Exception, e:
    raise Exception, 'CBANG_HOME not set?\n' + str(e)

import sys
from urlparse import urlparse
import urllib2
import tarfile
import shutil
import subprocess
import stat


version = '4.5.4'
package = 'gromacs-%s.tar.gz' % version
url = 'ftp://ftp.gromacs.org/pub/gromacs/' + package
patches = ['gromacs-4.5.4-fah.patch']


# Setup
env.CBLoadTools('compiler gromacs')
try:
    env.CBLoadTools('libfah')
except: pass
conf = env.CBConfigure()
env.__setitem__('strict', 0) # Force not strict


def CheckPipes(context):
    env = context.env

    context.Message('Checking for Pipes... ')

    source = """
      #include <stdio.h>
      int main() {return popen("/tmp/xyz", "r") != 0;}
    """

    if context.TryCompile(source.strip(), '.cpp'):
        env.AppendUnique(CPPDEFINES = ['HAVE_PIPES'])
        context.Result(True)
        return True

    context.Result(False)
    return False


def do_tar(package, extract):
    f = None
    tar = None
    try:
        f = open(package, 'rb') # Work around for Windows
        tar = tarfile.open(package, fileobj = f)

        if extract:
            sys.stdout.write('Extracting ' + package + '...')
            sys.stdout.flush()

            tar.extractall()

            sys.stdout.write('ok\n')
            sys.stdout.flush()

        return tar.getnames()[0]

    finally:
        if tar is not None: tar.close()
        if f is not None: f.close()


def extract(package):
    return do_tar(package, True)


def get_tar_root(filename):
    return do_tar(package, False)


def patch(root, patches):
    for patch in patches:
        sys.stdout.write('Applying patch ' + patch + '...')
        sys.stdout.flush()

        ret = subprocess.Popen(['python', 'patch.py', '-q', patch]).wait()
        if ret: raise Exception, 'Failed to apply patch ' + patch

        sys.stdout.write('ok\n')
        sys.stdout.flush()


def process_package(package, patches):
    extract(package)
    root = get_tar_root(package)
    patch(root, patches)
    os.utime(root, None)


def remove(path):
    if os.path.exists(path):
        if os.path.isdir(path): shutil.rmtree(path)
        else: os.unlink(path)


def flatten(l, ltypes = (list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else: l[i:i + 1] = l[i]
        i += 1
    return ltype(l)


# Download and unpack Gromacs package
clean_gromacs = False
if not os.path.exists(package):
    env.CBDownload(package, url)
    clean_gromacs = True

try:
    package_root = None
    package_root = get_tar_root(package)

    # Check for patch updates
    if os.path.exists(package_root):
        package_time = os.stat(package_root)[stat.ST_MTIME]

        for file in patches:
            if package_time < os.stat(file)[stat.ST_MTIME]:
                clean_gromacs = True
                break

    if clean_gromacs:
        remove(package_root)
        remove('gromacs')

    if not os.path.exists(package_root):
        process_package(package, patches)

except:
    # Redownload and try again
    remove(package)
    if package_root is not None: remove(package_root)
    remove('gromacs')
    
    env.CBDownload(package, url)
    process_package(package, patches)


# Copy Gromacs headers
if not os.path.exists('gromacs'):
    shutil.copytree(package_root + '/include', 'gromacs')


# Configure
if not env.GetOption('clean'):
    # Configure compiler
    if env['PLATFORM'] == 'win32': cstd = 'c99'
    else: cstd = 'gnu99'
    conf.CBConfig('compiler', cstd = cstd)

    functions = [
        '_aligned_malloc', '_commit', 'fileno', '_fileno', '_fseeki64',
        'fseeko', 'fsync', 'gettimeofday', 'memalign', 'posix_memalign',
        'strdup', 'swap', 'sysconf',
        ]
    headers = [
        'altivec', 'direct', 'dirent', 'regex', 'sys/time', 'sys/types',
        'sched', 'unistd', 'pthread', 'pwd', 'io', 'inttypes',
        ]


    # Headers
    for hdr in headers:
        if conf.CBCheckCHeader(hdr + '.h'):
            env.CBDefine('HAVE_' + hdr.replace('/', '_').upper() + '_H')

    # Functions
    for func in functions:
        if conf.CheckFunc(func):
            env.CBDefine('HAVE_' + func.upper())

    # Other dependencies
    conf.CBConfig('gromacs-deps')

    # Defines
    import socket
    import getpass
    import platform
    from datetime import datetime
    env.CBDefine([
            'VERSION="\\"%s\\""' % version,
            'GMXLIBDIR="\\"invalid\\""',
            'BUILD_TIME="\\"%s\\""' % 'undefined', #datetime.now().isoformat(),
            'BUILD_USER="\\"%s@%s\\""' % (getpass.getuser(),
                                          socket.gethostname()),
            'BUILD_MACHINE="\\"%s\\""' % platform.platform(),
            'GMX_DOUBLE',
            ])

    # Remove DEBUG define (Causes Gromacs compile failure in 4.5.4+)
    defines = env['CPPDEFINES']
    defines = filter(lambda d: not d.startswith('DEBUG'), flatten(defines))
    env.Replace(CPPDEFINES = defines)

    if env['PLATFORM'] == 'win32': env.CBDefine('RETSIGTYPE=int')
    else: env.CBDefine('RETSIGTYPE=void')

    # XDR
    if not conf.CBCheckCHeader('rpc/xdr.h'):
        env.CBDefine('GMX_INTERNAL_XDR')

    # libfah
    if env.get('fah', 0): conf.CBConfig('libfah')

    # Pipes
    conf.AddTest('CheckPipes', CheckPipes)
    conf.CheckPipes()

    # Windows
    if env['PLATFORM'] == 'win32': env.CBDefine('uid_t=int')

# Local includes
env.Append(CPPPATH = [package_root + '/include'])


# Build libs
libs = {
    'gmx': ['', 'selection', 'trajana', 'statistics', 'nonbonded',
            'nonbonded/nb_kernel_c'],
    'md': [''],
    }

for name, subdirs in libs.items():
    # Gather source
    src = []
    for dir in subdirs:
        src += Glob(package_root + '/src/%slib/%s/*.c' % (name, dir))
    src = map(str, src)

    # Filter out tests
    src = filter(lambda filename: filename.find('test') == -1, src)

    # Build
    Default(env.Library(name + '_d', src))

    # Find FAH source files
    if env.get('fah', 0):
        fahSrc = []
        nonFAHSrc = []
        for path in src:
            f = None
            try:
                f = open(path)
                if f.read().find('GMX_FAHCORE') != -1: fahSrc += [path]
                else: nonFAHSrc += [path]
            finally:
                if f is not None: f.close()

        # Build FAH lib
        fahObjs = []
        for path in fahSrc:
            fahObjs += [env.StaticObject(path, OBJPREFIX = 'fah-',
                                         CCFLAGS = '$CFLAGS -DGMX_FAHCORE=2')]

        Default(env.Library(name + '-fah', nonFAHSrc + fahObjs))
