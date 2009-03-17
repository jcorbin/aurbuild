#
#   aurparse.py
#
#   Copyright (C) 2005-2007 by Tyler Gates <TGates81@gmail.com>
#   Copyright (C) 2009 by Loui Chang <louipc.ist@gmail.com>
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

import re
import os
import sys
import urllib

"""
The format of the 'site' argument must be protocol://domain
ex: http://aur.archlinux.org
"""

# this looks a little strange but we need to access each of these
# functions (except aursearch) and query the server only once,
# hence the manual 'raw_text' parameters which is currentlyi
# obtained from raw_pkg_query().

def fix_path(str):
	str = re.sub('\\\\/', '/', str)
	return str

def raw_pkg_query(keyword, site):
	search_url = "%s/rpc.php?type=search&arg=%s" % (site, keyword)
	f = urllib.urlopen(search_url)
	lines = f.readlines()
	return lines

def pkg_info(pkg, site):
	search_url = "%s/rpc.php?type=info&arg=%s" % (site, pkg)
	f = urllib.urlopen(search_url)
	lines = f.readlines()
	return parse(lines)[0]

def pkg_main_url(pkg, site):
	raw_text = []

	try:
		raw_text = raw_pkg_query(pkg, site)
	except Exception, e:
		print >>sys.stderr.write(
			"Could not retrieve needed data from %s" % site)
		raise

	# Match the portion of the search for a specific package.
	url = re.search("ID\":\"()\",\"Name\":\"%s\"" % pkg, raw_text[0])
	url = "%s/rpc.php?type=info&arg=%s" % (site, url)

	return url

def pkg_tarball_url(pkgname, site):
	url = ''
	search_url = "%s/rpc.php?type=info&arg=%s" % (site, pkgname)
	f = urllib.urlopen(search_url)
	lines = f.readlines()

	for line in lines:
		if '"Name":"%s"' % pkgname in line:
			url = line.split('"URLPath":"')[1]
			url = url.split('",')[0]
			url = fix_path(url)
			break

	if url != '':
		return site + url
	else:
		return

def parse(f):
	"""
	Parses the output from the site's json interface.

	Returns an array of dicts that contain package info including:
	name, description, repo, maintainer, and votes.

	Note: maintainer isn't returned on the server side yet.
	"""
	# Implode
	data = ''
	for line in f:
		data += line

	# Clean up paths
	data = re.sub('\\\/', '/', data)

	results = data.split('"type":"')[1]
	results = results.split('","results":')
	type = results[0]
	results = results[1]
	
	if type == "error":
		results = results.split('"')[1]
		print results
		return

	# We could probably evaluate the output as python here,
	# but that may open up a security vulnerability.

	results = re.sub('","', '"\n"', results)

	# Probably don't need to do this.
	results = re.sub(r'"(\w+?)":"(.*)"', r'\1:\2', results)

	# Split up results.
	results = re.split('\[?\{', results, 1)[1]
	results = re.split('\}\]?\}', results, 1)[0]
	results = results.split('},{')

	for num in range(len(results)):
		temp = {}
		results[num] = results[num].splitlines()
		for num1 in range(len(results[num])):
			index, value = results[num][num1].split(':', 1)
			temp[index] = value 
		results[num] = temp

	packages = results

	repos = {
		'2': 'unsupported',
		'3': 'community'
	}

	# Compensate for some possible RPC flaws.
	for num in range(len(results)):
		try:
			results[num]['repo'] = repos[results[num]['LocationID']]
		except KeyError:
			results[num]['repo'] = 'aur';

		results[num]['maintainer'] = ''

	return packages

def aursearch(keyword, site):
	"""Perform a search."""

	return parse(raw_pkg_query(keyword, site))



if __name__ == '__main__':
	import sys
	print aursearch(sys.argv[1], 'http://aur.archlinux.org/')
	sys.exit(0)
