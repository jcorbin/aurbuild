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

import os, sys
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

def msg(text):
	if USE_COLOR == 'y':
		return '\033[1;32m==>\033[1;0m \033[1;1m' + text + '\033[1;0m'
	else:
		return '==> ' + text

def color(text, color_alias):
	if USE_COLOR == 'y':
		color_dict = {'grey':'0', 'red':'1', 'green':'2', 'yellow':'3', 'blue':'4', 'magenta':'5', 'cyan':'6', 'white':'7', 'black': '8'}
		return '\033[1;3' + color_dict[color_alias] + 'm' + text + '\033[1;0m'
	else:
		return text

def get_depends(pkgbuild, dep1, dep2):
	# dep1 is makedepends. dep2 is depends
	p = Popen('source ' + pkgbuild + '; echo "${' + dep1 + '[@]}:${' +
			dep2 + '[@]}"', shell=True, stdout=PIPE, stderr=PIPE)
	out = p.stdout.read()
	err = p.stderr.read()
	p.stdout.close()
	p.stderr.close()
	if err != '':
		print >>sys.stderr.write('\nPKGBUILD syntax error:\n\n' + err)
		cleanup()
		sys.exit(1)
	out = out.strip()
	out = out.split(':')
	dep1 = out[0].split(' ')
	dep2 = out[1].split(' ')
	return dep1, dep2

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

def user_makedirs(target, u_uid, u_gid):
		os.setegid(u_gid)
		os.seteuid(u_uid)
		os.makedirs(target)
		os.seteuid(uid)
		os.setegid(gid)


def prepare_work_dirs():
	try:
		cleanup()
		# parent directory of aurbuild_home should exist and owned by root
		if not os.path.isdir(os.path.dirname(aurbuild_home)):
			os.makedirs(os.path.dirname(aurbuild_home))

		# aurbuild_home should be root:aurbuild with 0775	
		if not os.path.isdir(aurbuild_home):
			os.mkdir(aurbuild_home)
			os.chmod(aurbuild_home, 0775)
			os.chown(aurbuild_home, 0, builduser_uid)

		# build_dir should be the same as aurbuild_home
		if not os.path.isdir(build_dir):
			os.mkdir(build_dir)
			os.chmod(build_dir, 0775)
			os.chown(build_dir, 0, builduser_uid)

		# pkg_build_dir should be created by the builduser
		user_makedirs(pkg_build_dir, builduser_uid, builduser_gid)
	except Exception, e:
		print >>sys.stderr.write('\ncould not prepare for build: ' + str(e) + '\n')
		sys.exit(1)

def prepare_build_user():
	global builduser_uid, builduser_gid
	try:
		builduser_uid = pwd.getpwnam('aurbuild')[2]
		builduser_gid = pwd.getpwnam('aurbuild')[3]
	except:
		# setup an account
		print 'creating designated build user... ',
		code = Popen(['useradd', '-s', '/bin/false', '-d', '/var/tmp/aurbuild', '-u', '360', '-c', 'aurbuild', 'aurbuild']).wait()
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
		prepare_build_user()
	

def get_tarball(pkg, pkg_query = None):
	if pkg_query == None: pkg_query = pkg
	
	try:
		raw_text = aaurparse.raw_pkg_query(pkg_query)
	except Exception, e:
		print >>sys.stderr.write('\ncould not retrieve needed data' +
			'from aur: ' + str(e))
		cleanup()
		sys.exit(1)

	main_url = aaurparse.pkg_main_url(raw_text, pkg)

	if main_url == '':
		print >>sys.stderr.write(pkg + ': not found in AUR')
		if UPGRADE: 
			return None
		else:
			cleanup()
			sys.exit(1)

	try:
		f = urllib.urlopen(main_url)
		raw_text = f.readlines()
		f.close()
	except IOError, e:
		print >>sys.stderr.write('\ncould not retrieve needed data from aur: '+main_url + ': ' + str(e) + '\n')
		cleanup()
		sys.exit(1)

	try:
		tarball_url = aaurparse.pkg_tarball_url(raw_text)
	except:
		print >>sys.stderr.write('\nUnable to parse tarball info. If you see this message rarely, it is\n' + 
						'possible user comments have skewed the parsing results on the web page.\n')
		cleanup()
		sys.exit(1)
	
	if tarball_url == '' and UPGRADE:
		return None
	elif tarball_url == '':
		print >>sys.stderr.write(pkg + ': possible [community] package')
		if SYNCDEPS:
			cmd = 'aurbuild --syncdeps --official '+pkg
		elif BUILDDEPS:
			cmd = 'aurbuild --builddeps --official '+pkg
		choice = raw_input('\nInstall by running `'+cmd+'\'? [Y/n]  ')
		if choice == '': choice = 'y'
		if NOCONFIRM: choice == 'y'
		choice = choice.lower()
		if choice == 'y' or choice == 'yes':
			retval = Popen(cmd, shell=True).wait()
			return None
		else:
			cleanup()
			sys.exit(1)


	try:
		tar = urllib.urlretrieve(tarball_url)[0]
		return tar
	except IOError, e:
		print >>sys.stderr.write('\ncould not retrieve needed data from aur: '+tarball_url + ': ' + str(e) + '\n')
		cleanup()
		sys.exit(1)

def extract(file):
	extract_dir = pkg_build_dir
	# split off the extension at `.'. Up to two allowed
	file_extension = file.rsplit('.', 2)[1:]
	if 'gz' in file_extension: ext = 'gz'
	elif 'tgz' in file_extension: ext = 'gz'
	elif 'bz2' in file_extension: ext = 'bz2'
	else:
		print >>sys.stderr.write('\n' + file + ': unsupported compression. Cannot extract.\n')
		cleanup()
		if os.path.exists(file): os.remove(file)
		cleanup()
		sys.exit(1)
	
	try:
		if os.path.isdir(extract_dir): rmtree(extract_dir)
		os.mkdir(extract_dir)
		os.chmod(extract_dir, 0775)
		os.chown(extract_dir, 0, builduser_gid) 
	except Exception, e:
		print >>sys.stderr.write('could not create temporary extraction point:')
		print >>sys.stderr.write(str(e))
		cleanup()
		sys.exit(1)

	try:
		tar_f = tarfile.open(file, 'r:' + ext)
		for member in tar_f.getmembers():
			tar_f.extract(member, extract_dir)
	except tarfile.TarError, e:
		print >>sys.stderr.write('\ncould not extract tarfile: ' + str(e) + '\n')
		if os.path.exists(file): os.remove(file)
		cleanup()
		sys.exit(1)

	# aur gives us fucked tarballs with nobody:nobody ownership... this will fix it
	def mod_extracted(dir):
		for d in os.listdir(dir):
			v = os.path.join(dir, d)
			os.chown(v, builduser_uid, builduser_gid)
			if os.path.isdir(v):
				mod_extracted(v)

	# the parent directory of the extracted tarball has a setgroup id bit set from AUR. This needs to be removed:
	for j in os.listdir(extract_dir):
		jf = os.path.join(extract_dir, j)
		if os.path.isdir(jf):
			os.chmod(jf, 0755)

	mod_extracted(extract_dir)

	tar_f.close()
	os.remove(file)

def get_PKGBUILD_path(parent_dir):
	results = Afind.find_file(parent_dir, 'PKGBUILD')[0]
	if results != []:
		results = results[0].replace('/PKGBUILD', '')
		return results
	else:
		print >>sys.stderr.write('\nPKGBUILD not found.\n')
		cleanup()
		sys.exit(1)

def filter_deps(pkg, fd_ct, type):
	""" give required dependency and return it if it needs to be installed or return group packages if it is that keyword
	filtered = [], list """
	# for tabbing over tree branch symbols
	pre_space  = 2
	# spaces must be greater than pre_space
	spaces = 3
	v = fd_ct/spaces
	indents = ' '*pre_space + ('|' + ' '*spaces)*v
	sys.stdout.write(color(indents + '`- ', 'blue') + color(pkg + ': ', 'black'))
	sys.stdout.flush()
	code = Apacman.operations().pacmanT(pkg)
	if code == 127:
		# see if its a group name
		group_pkgs = Apacman.db_tools().get_group(pkg)
		if group_pkgs == []:
			print color('missing ' + type, 'red')
			pkg = Apacman.db_tools().strip_ver_cmps(pkg)[0]
			if BUILDDEPS: 
				dep_path = get_dep_path(pkg)
				if dep_path != None:
					# a dependency is found, check it's deps and run this method again
					mdep_cans, dep_cans = get_depends(dep_path + '/PKGBUILD', 'makedepends', 'depends')
					if mdep_cans or dep_cans != ['']: fd_ct += spaces
					if mdep_cans != ['']:
						for mdep_can in mdep_cans:
							filter_deps(mdep_can, fd_ct, type='[M]')
					if dep_cans != ['']: 
						for dep_can in dep_cans:
							filter_deps(dep_can, fd_ct, type='[D]')
				else:
					print >>sys.stderr.write('\n' + pkg + ': not found in ABS.\n')
					cleanup()
					sys.exit(1)
			elif SYNCDEPS:
				# follows steps of BUILDDEPS omitting make dependencies
				if db_paths == []:
					# generate list to global
					db_paths.extend(Apacman.db_tools().get_db_pkgpaths())
				if db_pkgs == []:
					# generate list to global
					for db_path in db_paths:
						descfile = db_path + '/desc'
						if os.path.isfile(descfile):
							db_pkg = Apacman.db_tools().get_db_info(descfile, '%NAME%')[0]
							if db_pkg != []: db_pkgs.append(db_pkg)
				found = 0
				for db_pkg in db_pkgs:
					db_path = db_paths[db_pkgs.index(db_pkg)]
					if db_pkg != [] and pkg == db_pkg:
						found = 1
						dependsfile = db_path + '/depends'
						dep_cans = Apacman.db_tools().get_db_info(dependsfile, '%DEPENDS%')
						if dep_cans != []: 
							fd_ct += spaces
							for dep_can in dep_cans:
								filter_deps(dep_can, fd_ct, type='[D]')
				if not found:
					print >>sys.stderr.write('\n' + pkg + ': not found in database.\n')
					cleanup()
					sys.exit(1)
			# there must be no remaining deps of deps, add to list
			if not pkg in filtered: filtered.append(pkg)
		else:
			print color('group', 'cyan')
			fd_ct += 4
			for group_pkg in group_pkgs:
				filter_deps(group_pkg, fd_ct, type='[D]')
	elif code == 0:
		print color('ok ' + type, 'green')
		
	elif code != 127 and code != 0:
		sys.stderr.write('\naurbuild: fatal error while testing dependencies.\n')
		cleanup()
		sys.exit(1)
	return filtered


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

def install(pkgpath):
	if os.path.isfile(pacman_lock):
		print '\nPacman is detected running. Package cannot not be installed at this time.'
		print 'Once pacman exits, you may press enter to install this package. Control + C exits.'
		raw_input()	
	print msg('Leaving fakeroot environment...')
	# (makepkg will do it)
		
	print msg('Running pacman -U...')
	code = Popen(['pacman', '-U', pkgpath]).wait()
	if code > 0:
		print >>sys.stderr.write('\naurbuild: could not install package through pacman --upgrade.')
		cleanup()
		sys.exit(1)
			
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
			# ripped off from pydoc.py
			pipe = os.popen('less', 'w')
			try:
				for line in view_list:
					pipe.write(line)
				pipe.close()
			except IOError:
				# Ignore broken pipes caused be quitting less
				pass

def rm_dir_contents(dir):
	""" same as a rm -r dir/* """
	
	if not os.path.isdir(dir):
		return 1
	start_dir = dir.rstrip('/')
	
	# by starting a seperate function like this we will know when to stop the recursion by 
	# examining the 'static' start_dir variable from the parent function at each pass.
	def _rm_dir_contents(_dir):
		try:
			one_back = os.path.dirname(_dir)
			for each in os.listdir(_dir):
				object_path = os.path.join(_dir, each)
				if os.path.isdir(object_path) and not os.path.islink(object_path):
					if len(os.listdir(object_path)) == 0:
						os.rmdir(object_path)
					else:
						_rm_dir_contents(object_path)
				elif os.path.isfile(object_path) or os.path.islink(object_path):
					os.remove(object_path)
			if _dir == start_dir:
				return 0
			elif os.path.exists(one_back):
				_rm_dir_contents(one_back)
		except Exception, e:
			print >>sys.stderr.write('Error: unable to remove directory contents: '+str(e))
			return 1
	return _rm_dir_contents(start_dir)

