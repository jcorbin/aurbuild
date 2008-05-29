#!/usr/bin/python
#
#   utils.py
#
#   Copyright (C) 2005-2007 by Tyler Gates <TGates81@gmail.com>
#   Copyright (C) 2008 by Loui Chang <louipc.ist@gmail.com>
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

import os
import re
import sys
import pwd

from subprocess import Popen, PIPE
from shutil import copytree

import aurbuild

aaurparse = aurbuild.aurparse
afind = aurbuild.find

uid = os.getuid()
gid = os.getgid()

def color(text, color_alias):
	color_dict = {
		'grey': '0',
		'red': '1',
		'green': '2',
		'yellow': '3',
		'blue': '4',
		'magenta': '5',
		'cyan': '6',
		'white': '7',
		'black': '8'}
	return '\033[1;3%sm%s\033[1;0m'%(color_dict[color_alias], text)

def scan_pkgbuild(pkgbuild):
	"""
	Scan a PKGBUILD for problems and return an array of warnings.
	"""

	f = open(pkgbuild, 'r')
	lines = f.read().split('\n')
	f.close()

	can_has = []
	warnings = []
	for line in lines:
		if '#' in line:
			line = line.split('#', 1)[0]
		if re.search('arch=\(.+\)', line):
			can_has.append('arch')
			continue
		if re.search('license=\(.+\)', line):
			can_has.append('license')
			continue
		if re.search('license=\".+\"', line):
			can_has.append('license')
			continue

	if not 'arch' in can_has:
		warnings.append('Warning: PKGBUILD arch may not be defined.')

	if not 'license' in can_has:
		warnings.append('Warning: PKGBUILD license may not be defined.')

	return warnings
	
def bash_array(str):
	"""
	Return str as a call to a bash array.

	Example: myarray becomes ${myarray[@]}
	Use for clarity in a program rather
	than sprinkling '${' + str + '[@]}' everywhere
	"""

	return '${%s[@]}' % str

def echo_bash_vars(path, value):
	"""Return a variable from a bash file."""

	# Check if the value is an array
	if '[@]' in value:
		array = True
	else:
		array = False

	p = Popen('source %s; echo %s' % (path, value), shell=True,
			stdout=PIPE, stderr=PIPE)
	out = p.stdout.read()
	out = out.strip()

	if array:
		out = out.split(' ')

	p.stdout.close()
	err = p.stderr.read()
	p.stderr.close()

	if err != '':
		raise Exception('%s error:\n\t%s' % (path, err))

	return out
		
def cleanup():
	if os.path.isdir(pkg_build_dir):
		rmtree(pkg_build_dir)
	if aur_tarfile != None:
		if os.path.isfile(aur_tarfile):
			os.remove(aur_tarfile)

def handler(signo, frame):
	if signo == 2:
		cleanup()
		sys.exit(130)
	elif signo == 15:
		cleanup()
		sys.exit(143)

def get_depends(pkgbuild, makedeps='makedepends',
		deps='depends', optdeps='optdepends'):

	commands = 'source %s; echo -e "%s\n%s\n%s"' % (
		pkgbuild,
		bash_array(makedeps),
		bash_array(deps),
		bash_array(optdeps))

	p = Popen(commands, shell=True, stdout=PIPE, stderr=PIPE)
	out = p.stdout.read()
	err = p.stderr.read()
	p.stdout.close()
	p.stderr.close()

	if err != '':
		raise Exception('PKGBUILD error:\n\t%s' % err)

	out = out.splitlines()
	makedeps = out[0].split(' ')
	deps = out[1].split(' ')
	optdeps = out[2].split(' ')
	return makedeps, deps

def get_dep_path(abs_root, dep):
	if not os.path.isdir(abs_root):
		raise Exception('\n%s not found in filesystem.'
			'Cannot build dependencies\n' % abs_root)

	results = afind.find_dir(abs_root + '/', dep)

	if results != None:
		for p in results:
			if os.path.isfile(p + '/PKGBUILD'):
				return p

	raise Exception('%s: not found in ABS.\n' % dep)

def user_copytree(target, des, u_uid, u_gid):
	os.setegid(u_gid)
	os.seteuid(u_uid)
	copytree(target, des)
	os.seteuid(uid)
	os.setegid(gid)

# Only use this function for individual pkg build directories
def user_makedirs(target, u_uid, u_gid):
	os.setegid(u_gid)
	os.seteuid(u_uid)

	os.makedirs(target)
	os.seteuid(uid)
	os.setegid(gid)

def prepare_build_user():
	"""
	Prepare the aurbuild user.

	Create the user if it doesn't exist, otherwise
	returns a tuple containing the uid, and gid.
	"""

	try:
		builduser_uid = pwd.getpwnam('aurbuild')[2]
		builduser_gid = pwd.getpwnam('aurbuild')[3]
		return builduser_uid, builduser_gid  
	except:
		# setup an account
		print 'creating designated build user... ',
		code = Popen(['useradd', 
			'-s', '/bin/false',
			'-d', '/var/tmp/aurbuild',
			'-u', '360',
			'-c', 'aurbuild', 'aurbuild']).wait()
		if code != 0:
			raise Exception('Error: could not create designated '
				'build user. '
				'Reports exit status %s' % str(code))
		else:
			print 'done.'
		
		# lock password
		print 'locking password... ',
		code = Popen(['passwd', '-l', '-q', 'aurbuild']).wait()
		if code != 0:
			raise Exception('Error: could not lock password. '
				'Reports exit status of %s' % str(code))
		else:
			print 'done.'
		
		# prepare_work_dirs() will handle the proper build directories
		
		# try again
		return prepare_build_user()

def get_pkgbuild_path(parent_dir):
	results = afind.find_file(parent_dir, 'PKGBUILD')
	if results != None:
		results = results[0].replace('/PKGBUILD', '')
		return results
	else:
		raise Exception('PKGBUILD not found.\n')

def appcheck(app):
	path = os.getenv('PATH')
	path = path.replace(':', '/ ')
	path = path.split(' ')
	for each in path:
		if os.path.isfile(each + app): return True
	return False

def search(args, verbose, site):
	import textwrap

	try:
		names, descriptions, locations, categories, maintainers, \
			votes = aaurparse.aursearch(args[0], site) 
	except Exception, e:
		print >>sys.stderr.write(str(e))
		sys.exit(1)

	if names == None:
		print >>sys.stderr.write(args[0] + ': search results empty')
		sys.exit(1)
	else:
		view_list = []
		for num in range(len(names)):
			name 		= names[num]
			desc	 	= textwrap.wrap(descriptions[num]) 
			location	= locations[num]
			category	= categories[num]
			maintainer	= 'Maintainer: ' + maintainers[num] 
			_votes		= 'Votes: ' + votes[num] + '\n'


			description = ''
			for line in desc:
				description += '\t%s\n' % line

			if category != '':
				category = '(%s)' % category

			pkg_info = '%s/%s %s\n%s' % (
				location, name, category, description) 

			if verbose:
				pkg_info += '\t%s\n\t%s' % (maintainer, _votes)

			pkg_info += '\n'

			view_list.append(pkg_info)

		if not appcheck('less'):
			for each in view_list:
				print each
		else:
			pipe = os.popen('less', 'w')
			try:
				for line in view_list:
					pipe.write(line)
				pipe.close()
			except IOError:
				# Ignore broken pipes caused be quitting less
				pass


