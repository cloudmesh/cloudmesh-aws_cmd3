from setuptools import find_packages, setup
import re


def readfile(path):
    with open(path) as fd:
        return fd.read()


def setuptools_requires(path):
    """
    Get the package names from the requirements file
    
    This strips any version pinning from each specification
    """
    reqs = []

    pkgname_pypi_re = re.compile(r'^(?P<pkg>[a-zA-Z0-9-_.]+)')

    with open(path) as fd:
        for line in fd:
            l = line.strip()
            if not l: continue
            if l.startswith('#'): continue

            m = pkgname_pypi_re.match(l)
            if m:
                pkg = m.group('pkg')
                reqs.append(pkg)
            else:
                msg = "I don't know how to parse package name from: %r" % l
                raise NotImplementedError(msg)

    return reqs


setup(
    name = 'cloudmesh.aws',
    author = "Gregor von Laszewski, Badi' Abdul-Wahid",
    version = readfile('VERSION').strip(),
    license = 'Apache 2.0',
    namespace_packages = ['cloudmesh'],
    packages = find_packages(),
    install_requires = setuptools_requires('requirements.open'),
    tests_require = setuptools_requires('requirements.dev'),
)
