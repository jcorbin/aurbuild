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


'''
' Uses unix `find` to find files and/or directories
' Pass parameters according to standard find usage
'	find dir -type type -name name
'
' Returns a tuplet of two arrays
'	search results
'	any error messages
'
' Hardcoded maxdepth will cause problems if the ABS tree goes deeper than
' three levels.
'''
def find_it(dir, name, type):
	from subprocess import Popen, PIPE
	output, error = Popen(
		['find', dir,
		'-maxdepth', '3',
		'-type', type,
		'-name', name],
		stdout=PIPE).communicate()
	result = output.splitlines()

	return result, [error]

'''
' Recursively search for directories from a starting directory
' dir: starting directory
' name: name of directory
'''
def find_dir(dir, name):
	return find_it(dir, name, 'd');
	

'''
' Recursively search for files from a starting directory
' dir: starting directory
' name: name of file
'''
def find_file(dir, name):
	return find_it(dir, name, 'f')

