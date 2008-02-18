#!/usr/bin/python
#
#   execute.py
#
#   Copyright (C) 2007 by Tyler Gates <TGates81@gmail.com>
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

def get_app_path(app):
	path = os.getenv('PATH').split(':')
	for p in path:
		candidate = os.path.join(p, app)
		if os.access(candidate, os.F_OK | os.X_OK):
			return candidate
	# must not be found, return none
	return None


def child_spawn(app, args, uid=None, gid=None, env={}):
	original_uid = os.getuid()
	original_gid = os.getgid()
	# set effective uid to uid temporarily to test for execute permissions
	if uid == None: uid = os.getuid()
	try:
		os.seteuid(uid)
	except:
		print >>sys.stderr.write('Error: unable to switch uid to '+str(uid)+'. This may result in root access to builds, \
				proceed at your own risk!.')
		pass
	
	if os.path.isabs(app) and os.access(app, os.F_OK | os.X_OK):
		# good 
		path = app
		app = os.path.basename(path)
	elif not os.path.isabs(app):
		# find it's path
		path = get_app_path(app)
		if path == None:
			print >>sys.stderr.write('Error: `'+app+'\' not found in PATH or is not accessible to uid '+str(uid)+'.')
			sys.exit(1)
		app = os.path.basename(path)
	# set effective uid back
	os.seteuid(original_uid)
	
	# args must be a list
	if not isinstance(args, list):
		args = args.split()
		# add the binary to the front of the list 
		args[:0] = app
	
	fpid = os.fork()
	if not fpid:
		if gid != None: os.setgid(gid)
		if uid != None: os.setuid(uid)
		if env == {}: env = os.environ
		os.execve(path, args, env)
	retcode = os.waitpid(fpid, 0)[1]
	return retcode

