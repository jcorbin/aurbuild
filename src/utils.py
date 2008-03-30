#!/usr/bin/python
#
#   utils.py
#
#   Copyright (C) 2005-2007 by Tyler Gates <TGates81@gmail.com>
#   Copyright (C) 2008 by Loui Chang <louipc.ist@gmail.com>
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

import os, sys, pwd
from subprocess import Popen, PIPE
from shutil import copytree

uid			= os.getuid()
gid			= os.getgid()

import aurbuild
aaurparse = aurbuild.aurparse
afind = aurbuild.find

'''
' Return a variable from a bash file
' The array parameter is to specify whether you're expecting an array
'
'''
def echo_bash_vars(path, value, array=False):
	p = Popen('source ' + path + '; echo '+value, shell=True,
			stdout=PIPE, stderr=PIPE)
	out = p.stdout.read()
	out = out.strip()

	if array:
		out = out.split(' ')

	p.stdout.close()
	err = p.stderr.read()
	p.stderr.close()

	if err != '':
		raise Exception(err)

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

def get_depends(pkgbuild, makedeps, deps):

	p = Popen('source ' + pkgbuild +
		'; echo "${' + makedeps + '[@]}:${' +
		deps + '[@]}"', shell=True, stdout=PIPE, stderr=PIPE)

	out = p.stdout.read()
	err = p.stderr.read()
	p.stdout.close()
	p.stderr.close()

	if err != '':
		raise Exception("PKGBUILD syntax error:\n\t" + err)

	out = out.strip()
	out = out.split(':')
	makedeps = out[0].split(' ')
	deps = out[1].split(' ')
	return makedeps, deps

def get_dep_path(abs_root, dep):
	if not os.path.isdir(abs_root):
		print >>sys.stderr.write('\n' + abs_root + 'not found in filesystem. Cannot build dependencies\n')
		cleanup()
		sys.exit(1)
	results = afind.find_dir(abs_root + '/', dep)[0]
	if results != []:
		for p in results:
			if os.path.isfile(p + '/PKGBUILD'):
				return p
		return None
	else:
		return None

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

'''
' Prepare aurbuild user
' Returns a tuple: aurbuild uid, and gid
'''
def prepare_build_user():
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
			print >>sys.stderr.write('Error: could not create designated build user. Reports exit status '+str(code)+'. ')
			sys.exit(1)
		else: print 'done.'
		
		# lock password
		print 'locking password... ',
		code = Popen(['passwd', '-l', '-q', 'aurbuild']).wait()
		if code != 0:
			print >>sys.stderr.write('Error: could not lock password. Reports exit status of '+str(code))
			sys.exit(1)
		else:
			print 'done.'
		
		# prepare_work_dirs() will handle the proper build directories
		
		# try again
		return prepare_build_user()
	

def get_PKGBUILD_path(parent_dir):
	results = Afind.find_file(parent_dir, 'PKGBUILD')[0]
	if results != []:
		results = results[0].replace('/PKGBUILD', '')
		return results
	else:
		print >>sys.stderr.write('\nPKGBUILD not found.\n')
		cleanup()
		sys.exit(1)

def src_to_pm_cache(sources):
	""" copy the sources in raw format (from sources array) to pacman cache """

	cwd = os.getcwd()
	if SRCDEST == '':
		_SRCDEST = os.path.join(pm_cache, 'src')
	else:
		_SRCDEST = SRCDEST
	for source in sources:
		source_file = source.split('/')[-1]
		try:
			source_file = os.path.join(cwd, 'src', source_file)
			copy(source_file, _SRCDEST)
		except:
			pass

			
def appcheck(app):
	path = os.getenv('PATH')
	path = path.replace(':', '/ ')
	path = path.split(' ')
	for each in path:
		if os.path.isfile(each + app): return True
	return False

def savefiles(pkg, old_dir):
	failed = 0
	def abort_msg(msg):
		print >>sys.stderr.write('Error saving ' + pkg + ' to ' + save_dir + ': ' + msg)
		print >>sys.stderr.write('Aborting save...')
		
	savecan = os.path.join(save_dir, pkg)
	if not os.path.isdir(save_dir):
		try:
			os.makedirs(save_dir)
			os.chmod(save_dir, 0775)
			os.chown(save_dir, 0, builduser_uid)
		except OSError, e:
			abort_msg(str(e))
			failed = 1
	
	if os.path.isdir(savecan) and not failed:
		if not NOCONFIRM: choice = raw_input('`' + savecan + '\': directory exists. Overwrite? [Y/n]  ').lower()
		if NOCONFIRM or choice == 'y' or choice == 'yes' or choice == '':
			try:
				rmtree(savecan)
				user_copytree(old_dir, savecan, builduser_uid, builduser_gid)
			except OSError, e:
				abort_msg(str(e))
				failed = 1
	elif not os.path.isdir(savecan) and not failed:
		try:
			user_copytree(old_dir, savecan, builduser_uid, builduser_gid)
		except OSError, e:
			abort_msg(str(e))

def search(args, verbose, site):
	import textwrap
	try:
		names, descriptions, locations, categories, maintainers, votes = aaurparse.aursearch(args[0], site) 
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
				description += '\t' + line + '\n'

			if category != '':
				category = '(' + category + ')'

			pkg_info = location + '/' + name + ' ' + category + \
				'\n' + description 

			if verbose:
				pkg_info += '\t' + maintainer + '\n\t' + _votes

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


