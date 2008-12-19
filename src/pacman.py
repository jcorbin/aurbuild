#
#   pacman.py
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
import sys
import re

from subprocess import Popen, PIPE

from aurbuild.version import vercmp

class PacmanError(Exception):
	# base excpetion
	pass

class DatabaseError(PacmanError):
	# general database errors
	pass

class ConfigError(PacmanError):
	# general configuration file errors
	pass

class db_tools:
	def __init__(self):
		self.pacman_db 		= '/var/lib/pacman'
		self.installed_db 	= self.pacman_db + '/local'
		self.pacman_db		= self.pacman_db + '/sync'
		self.pacman_config 	= '/etc/pacman.conf'
		self.comparators 	= ['<=', '>=', '=']

	def get_query(self, query):
		command = "pacman"
		output = Popen([command,query], stdout=PIPE).communicate()[0]
		
		names = []
		versions = []
		output = output.splitlines()
		for line in output:
			name, sep, version = line.partition(' ')
			names.append(name)
			versions.append(version)

		return names, versions

	def file_contents(self, file):
		"""
		Return a file as a list of lines.
		"""

		f = open(file, 'r')
		list = f.read().split('\n')
		f.close()
		return list

	def strip_ver_cmps(self, package):
		"""
		Separate pkgname, comparator (if it exists), and version
		from a versioned dependency.

		Return the three as a tuple.
		"""
		
		stripped = package
		comp = None
		version = None

        	for comparator in self.comparators:
                	stripped = stripped.split(comparator)
	                if len(stripped) > 1:
				comp = comparator
        	                return stripped[0], comp, stripped[1]
			else:
				stripped = stripped[0]
		return stripped, comp, version

	def check_installed(self, pkgname, logical=True):
		"""
		Check if a package is installed. If so, return its path.
		"""

		if not os.path.isdir(self.installed_db):
			raise DatabaseError('pacman local database %s'
				' was not found' % self.installed_db)

		cans = os.listdir(self.installed_db)
		for can in cans:
			pkgpath = self.installed_db + '/' + can
			if os.path.isdir(pkgpath) and not os.path.islink(pkgpath):
				descfile = pkgpath + '/desc'
				dependsfile = pkgpath + '/depends'
				if not os.path.isfile(descfile):
					raise DatabaseError('Database description file %s not found.' % descfile)
				if not os.path.isfile(dependsfile):
					raise DatabaseError('Database depends file %s not found' % dependsfile)
				name = self.get_db_info(descfile, '%NAME%')
				provides = self.get_db_info(dependsfile, '%PROVIDES%')
				for e in name: 
					if e == pkgname: return pkgpath
				if logical:
					for j in provides:
						if j == pkgname: return pkgpath
		return False

	def get_db_info(self, dbfile, info):
		"""Get database information info from dbfile."""
		
		# this is all written this speed in mind
		if not os.path.isfile(dbfile):
			raise DatabaseError('Database file %s was not found.' % dbfile)
		lines = self.file_contents(dbfile)
		results = []
		for num in range(len(lines)):
			if info in lines[num]:
				# get everything below info word
				try:
					below_info = lines[num+1:]
				except IndexError:
					# no white space after info word should be rare but return the empty list to the user
					return results
				for entry in below_info:
					# add to results list until white space
					if entry != '': results.append(entry)
					else: return results
		return results

	def get_repos(self):
		"""Read pacman.conf and return a list of enabled repos."""

		if not os.path.isfile(self.pacman_config):
			raise ConfigError('Configuration file %s not found' % self.pacman_config)
		contents = self.file_contents(self.pacman_config)
		repolist = []
		for line in contents:
			# ignore comments
			if '#' in line:
				line = line.split('#', 1)[0]
			if re.search('\[.*\]', line)  and not re.search('\[options\]', line):
				line = line.split('[', 1)[1]
				line = line.split(']', 1)[0]
				repolist.append(line.strip())
		return repolist

	def get_db_pkgpaths(self):
		"""
		Get a list of all package database paths according to
		specified repos in /etc/pacman.conf
		"""

		#pkgpaths = [], list

		pkgpaths = []
		repo_names = self.get_repos()
		for repo_name in repo_names:
		        # add the path to repo names and check it exists, if so list it to get pakage directories
			if not os.path.isdir(self.pacman_db):
				raise DatabaseError('Root database %s not found' % self.pacman_db)
			repo_path = self.pacman_db + '/' + repo_name
			if os.path.isdir(repo_path) and not os.path.islink(repo_path):
				# get the files from package directories in each reop
				for e in os.listdir(repo_path):
					can = repo_path + '/' + e
					if os.path.isdir(can) and not os.path.islink(can): pkgpaths.append(can)
		return pkgpaths

	def get_group(self, keyword):
		"""
		Scan repo database for keyword as a group and return all
		packages included in the group. 
		"""

		packages = []
		pkg_paths = self.get_db_pkgpaths()
		for pkg_path in pkg_paths:
			# don't raise an exception here because these database files don't necessarily have to be there
			descfile = pkg_path + '/desc'
			if os.path.isfile(descfile):
				group_names = self.get_db_info(descfile, '%GROUPS%')
				if keyword in group_names:
					try:
						tmp = self.get_db_info(descfile, '%NAME%')[0]
					except IndexError:
						raise DatabaseError(
							'Error: unable to parse NAME from database file %s'
							'. Possible corruption.\n' % descfile)
					if tmp != []: packages.append(tmp)
		return packages

	def get_local(self):
		"""
		Returns two dictionaries of pkgname and pkgver of all
		locally installed packages.
		"""

		query = "-Q"
		names = []
		versions = []

		try:
			# Set these two dictionaries
			names, versions = self.get_query(query) 
		except IndexError:
			raise DatabaseError(
				'ERROR: pacman failure or empty set.')

		return names, versions

	def get_foreign(self):
		"""
		Return two dictionaries of pkgname and pkgver of installed
		packages which aren't in the official repos.
		"""

		query = "-Qm"
		names = []
		versions = []

		try:
			# Set these two dictionaries
			names, versions = self.get_query(query) 
		except IndexError:
			raise DatabaseError(
				'ERROR: pacman failure or empty set')

		return names, versions

def syncdeps(deplist):
	"""
	Install dependencies before starting the build.

	This is synonymous with --syncdeps switch in aurbuild.
	"""

	pkglist = []
	pkgstring = ''
	for pkg in deplist:
		if pkg != '':
			pkg = db_tools().strip_ver_cmps(pkg)[0]
			pkglist.append(pkg)

	cmd = ['pacman', '-S', '--asdeps', '--noconfirm']
	cmd.extend(pkglist)

	code = Popen(cmd).wait()
	if code == 127:
		raise PacmanError('pacman could not install dependencies.\n')

class operations(db_tools):

	def pacmanT(db_tools, dependency):
		"""
		Test if the dependency needs to be installed.

		Returns:
			0: satisfied
			2: something bad happened
			127: missing
		"""

		pkgname, comp, req_version = db_tools.strip_ver_cmps(dependency)
		pkgpath = db_tools.check_installed(pkgname)

		if not pkgpath:	return 127

		try:
			inst_version = db_tools.get_db_info(pkgpath + '/desc', '%VERSION%')[0]
		except IndexError:
			raise DatabaseError(
				'Error: unable to parse VERSION information '
				'in local database file %s/desc. Possible '
				'corruption.\nTry re-installing %s.' %
				(pkgpath, os.path.basename(pkgpath)))

		
		# If the dependency did not have a release number, remove it
		# from the installed for a fair comparison. We are concerned
		# with package's version number.
		if not re.search('-[0-9]*$', dependency): 
			inst_version = re.sub('-[0-9]*$', '', inst_version)

		if inst_version != None:
			if comp == None: return 0
			elif req_version == None: return 0
			elif comp == '>=': 
				if vercmp().vercmp(inst_version, req_version) >= 0: return 0
				else: return 127
			elif comp == '<=':
				if vercmp().vercmp(inst_version, req_version) <= 0: return 0
				else: return 127
			else:
				if vercmp().vercmp(inst_version, req_version) == 0: return 0
				else: return 127
		# something bad must have happened, return 2
		else: return 2

if __name__ == '__main__':
	import sys
	print operations().pacmanT(sys.argv[1])
	sys.exit(0)
