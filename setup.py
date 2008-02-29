#!/usr/bin/python

NAME="aurbuild"
VERSION="1.8.1"
DESC="An utility to build and install packages from Archlinux User Repository"
AUTHOR="Tyler Gates, Loui Chang"
EMAIL="TGates81@gmail.com, louipc.ist@gmail.com"
LICENSE="GPL"

from distutils.core import setup

DATAFILES = [('/usr/man/man1', ['aurbuild.1']),
		('/usr/share/doc/aurbuild-'+VERSION,
		['COPYING', 'README', 'AUTHORS', 'CHANGELOG'])]

setup(name="aurbuild",
	version=VERSION,
	description=DESC,
	author=AUTHOR,
	author_email=EMAIL,
	license=LICENSE,
	platforms="linux2",
	packages=['aurbuild'],
	package_dir={'aurbuild':'src'},
	scripts=['scripts/aurbuild'], 
	data_files = DATAFILES)


