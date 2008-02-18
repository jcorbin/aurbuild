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

def find_dir(dir, name):
	""" find_dir(dir, name) -> results, errors 
    	searches recursively in directory dir for directory name. Symlinks are omitted."""

	def findit(dir, name):
		cans = []
		# add the trailing `/' now if it doesn't exist. This is about 25% faster than using os.path.join()
		if dir[-1:] != '/': dir = dir + '/'
		if os.path.isdir(dir) and not os.path.islink(dir):
			try:
				cans = os.listdir(dir)
			except Exception, e:
				errors.append(str(e))

			if cans != []:
				for can in cans:
					fullpath = dir + can
					if os.path.islink(fullpath): continue
					elif os.path.isdir(fullpath):
						if can == name: results.append(fullpath)
						findit(fullpath, name)
	
		return results, errors
	import os
	results	= []
	errors	= []
	return findit(dir, name)
	

def find_file(dir, name):
	""" find_file(dir, name) -> results, errors
	searches recursively in directory dir for file name. Symlinks are omitted."""

	def findit(dir, name):
		cans = []
		if dir[-1:] != '/': dir = dir + '/'
		if os.path.isdir(dir) and not os.path.islink(dir): 
			try:
				cans = os.listdir(dir)
			except Exception, e:
				errors.append(str(e))
			if cans != []:
				for can in cans:
					fullpath = dir + can
					if os.path.islink(fullpath): continue
					elif os.path.isfile(fullpath):
						if can == name: results.append(fullpath)
					else:
						findit(fullpath, name)

		return results, errors
	import os
	results	= []
	errors	= []
	return findit(dir, name)

