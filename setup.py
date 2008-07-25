#!/usr/bin/python

from distutils.core import setup

NAME = "aurbuild"
VERSION = "1.8.4"
DESC = "An utility to build and install packages from Arch Linux User Repository"
LICENSE = "GPL"
URL = "http://aurbuild.berlios.de"
AUTHOR = "Tyler Gates, Loui Chang"
EMAIL = "TGates81@gmail.com, louipc.ist@gmail.com"

DATAFILES = [('/usr/man/man1', ['aurbuild.1']),
		('/usr/share/aurbuild-' + VERSION,
		['BUGS', 'COPYING', 'README', 'AUTHORS'])]

setup(
	name = NAME,
	version = VERSION,
	description = DESC,
	url = URL,
	author = AUTHOR,
	author_email = EMAIL,
	license = LICENSE,
	platforms = "linux2",
	packages = ['aurbuild'],
	package_dir = {'aurbuild':'src'},
	scripts = ['scripts/aurbuild'], 
	data_files = DATAFILES)

