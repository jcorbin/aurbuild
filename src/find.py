#
#   find.py
#
#   Copyright (C) 2008 Loui Chang <louipc.ist@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2
#   as published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#


def find_it(dir, name, type):
	"""
	Use unix `find` to find files and/or directories.

	This function only supports two parameters.
	Pass parameters according to standard find usage.
		find dir -type type -name name

	Return two arrays.
		search results
		any error messages

	Hardcoded maxdepth will cause problems if the ABS tree goes deeper
	than three levels.
	"""

	import os
	import sys
	from subprocess import Popen, PIPE

	# Test for dir's existence.
	if not os.access(dir, os.F_OK | os.R_OK):
		print >> sys.stderr.write('Error: %s not found or read permissions denied.' % dir)
		return None

	output, error = Popen(
		['find', dir,
		'-maxdepth', '3',
		'-type', type,
		'-name', name],
		stdout=PIPE).communicate()

	if error:
		raise Exception(str(error))

	result = output.splitlines()

	if result == []:
		return None

	return result

def find_dir(dir, name):
	"""
	Recursively search for directories from a starting directory.

	dir: starting directory
	name: name of directory
	"""

	return find_it(dir, name, 'd');


def find_file(dir, name):
	"""
	Recursively search for files from a starting directory.

	dir: starting directory
	name: name of file
	"""

	return find_it(dir, name, 'f')

