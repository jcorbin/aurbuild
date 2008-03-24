#!/usr/bin/python
#
#   utils.py
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

import os, sys, pwd
from subprocess import Popen, PIPE
from shutil import copytree

uid			= os.getuid()
gid			= os.getgid()

import aurbuild
aaurparse = aurbuild.aurparse
afind = aurbuild.find

def echo_bash_vars(path, value, array=False):
	""" return a variable from a bash file """
	
	p = Popen('source '+path+'; echo '+value, shell=True,
			stdout=PIPE, stderr=PIPE)
	out = p.stdout.read()
	out = out.strip()
	if array:
		out = out.split(' ')
	p.stdout.close()
	err = p.stderr.read()
	p.stderr.close()
	return out, err
		
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
		print >>sys.stderr.write('\nPKGBUILD syntax error:\n\n' + err)
		err = 1

	out = out.strip()
	out = out.split(':')
	makedeps = out[0].split(' ')
	deps = out[1].split(' ')
	return makedeps, deps, err

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

def get_pkgpath():
	""" get the built package path """

	cwd = os.getcwd()
	if PKGDEST == '':
		_PKGDEST = cwd
	else:
		_PKGDEST = PKGDEST
	
	out, err = echo_bash_vars(os.path.join(cwd, 'PKGBUILD'), '${pkgname}%${pkgver}%${pkgrel}')
	if err != '':
		print >>sys.stderr.write('PKGBUILD syntax error: '+err)
		cleanup()
		sys.exit(1)

	out = out.split('%')
	pkgname, pkgver, pkgrel = out[0], out[1], out[2]

	v2_pkgpath = os.path.join(_PKGDEST, pkgname+'-'+pkgver+'-'+pkgrel+'.'+PKGEXT)
	v3_pkgpath = os.path.join(_PKGDEST, pkgname+'-'+pkgver+'-'+pkgrel+'-'+CARCH+'.'+PKGEXT)

	if os.path.exists(v2_pkgpath):
		pkgpath = v2_pkgpath
	elif os.path.exists(v3_pkgpath):
		pkgpath = v3_pkgpath
	else:
		print >>sys.stderr.write('Error: could not find the built package.')
		print >>sys.stderr.write('In some cases this might mean the PKGDEST location does not have write and execute permissions')
		print >>sys.stderr.write('for the `aurbuild\' user or group.')
		cleanup()
		sys.exit(1)
	
	return pkgpath

def makepkgf(dep):

	cwd = os.getcwd()
	raw_sources, err = echo_bash_vars(os.path.join(cwd, 'PKGBUILD'), '${source[@]}', array=True)
	if err != '':
		print >>sys.stderr.write('PKGBUILD syntax error: '+err)
		cleanup()
		sys.exit(1)
	
	app = 'makepkg'
	args = ['makepkg', '-f']
	if BUILDER_OPTS and BUILDER_OPTARGS != '':
		args.extend(BUILDER_OPTARGS.split(' '))
	
	# ccache needs a writable HOME, set it here.
	env = os.environ
	env['HOME'] = aurbuild_home
	code = Aexec.child_spawn(app, args, builduser_uid, builduser_gid, env)

	# copy src files over to cache
	src_to_pm_cache(raw_sources)

	if code > 0:
		print >>sys.stderr.write('\naurbuild: could not build \"' + dep + '\" with makepkg.')
		print 'build directory retained at `'+pkg_build_dir+'\''
		print 'In some cases you may be able to cd into the directory, fix the problem and run makepkg with success.'
		sys.exit(1)
	
	return get_pkgpath()

			
def builddeps(deplist):
        # for -b option
	cwd = os.getcwd()
        for each in deplist:
                dep_path = get_dep_path(each)
                if dep_path == None:
                        print >>sys.stderr.write('\naurbuild: dependency \"' + each + '\" not found in abs.')
                        cleanup()
                        sys.exit(1)

		des_dir = os.path.join(build_dir, each)
		os.setegid(builduser_gid)
		os.seteuid(builduser_uid)
                copytree(dep_path, des_dir)
		os.seteuid(uid)
		os.setegid(gid)
                os.chdir(des_dir)
		pkgpath = makepkgf(each)
		if not NOINSTALL: install(pkgpath)

        os.chdir(cwd)
	
def syncdeps(deplist):
	# for -s option
	pkglist = []
	pkgstring = ''
	for pkg in deplist:
		if pkg != '':
			pkg = Apacman.db_tools().strip_ver_cmps(pkg)[0]
			pkglist.append(pkg)
	
	cmd = ['pacman', '-S', '--noconfirm']
	cmd.extend(pkglist)
			
	code = Popen(cmd).wait()
	if code == 127:
		sys.stderr.write('\naurbuild: pacman could not install dependencies.\n')
		cleanup()
		sys.exit(1)

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

def search(args, verbose):
	import textwrap
	try:
		names, descriptions, locations, categories, maintainers, votes = aaurparse.aursearch(args[0]) 
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


