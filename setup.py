#!/usr/bin/python

from distutils.core import setup

myver="1.7.8"
DATAFILES = [('/usr/man/man1', ['aurbuild.1']), ('/usr/share/doc/aurbuild-'+myver, ['COPYING', 'README', 'AUTHORS', 'CHANGELOG'])]

setup(name="aurbuild",
	version=myver,
	description="A utility to build and install packages from ArchLinux' AUR",
	author="Tyler Gates",
	author_email="TGates81@gmail.com",
	license="GPL",
	platforms="linux2",
	packages=['Aurbuild'], scripts=['aurbuild'], data_files = DATAFILES)


