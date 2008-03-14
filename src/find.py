#
#   find.py
#
#   Copyright (C) 2005-2007 by Tyler Gates <TGates81@gmail.com>
#  
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#  
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, 
#   USA.
#


'''
' Uses unix `find` to find files and/or directories
' Pass parameters according to standard find usage
'	find dir -type type -name name
'''
def find_it(dir, name, type):
	from subprocess import Popen, PIPE
	output, error = Popen(
		['find', dir, '-type', type, '-name', name],
		stdout=PIPE).communicate()
	result = output.splitlines()

	return result, [error]

'''
' find_dir(dir, name) -> results, errors 
' searches recursively in directory dir for directory name.
' Symlinks are omitted.
'''
def find_dir(dir, name):
	return find_it(dir, name, 'd');
	

'''
' find_file(dir, name) -> results, errors
' searches recursively in directory dir for file name. Symlinks are omitted.
'''
def find_file(dir, name):
	return find_it(dir, name, 'f')

