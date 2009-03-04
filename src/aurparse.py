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
	search_url = "%s/rpc.php?type=search&arg=" % site
	f = urllib.urlopen(search_url + keyword)
	lines = f.readlines()
	return lines

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
def aursearch(keyword, site):
	"""
	Gets and parses the output from the site's search page.

	Returns a set of arrays that contain the package info in the order of:
	names, descriptions, locations, categories, maintainers, and votes.
	"""

	f = raw_pkg_query(keyword, site)

	# Implode
	data = ''
	for line in f:
		data += line

	results = data.split('"type":"')[1]
	results = results.split('","results":')
	type = results[0]
	results = results[1]

	if type == "error":
		results = results.split('"')[1]
		print results
		return

	# Clean up paths
	results = re.sub('\\\/', '/', results)
	results = re.sub('","', '"\n"', results)
	results = re.sub(r'"(\w+?)":"(.+?)"', r'\1:\2', results)

	# Split up results.
	results = results.split('[{')[1]
	results = results.split('}]}')[0]
	results = results.split('},{')
	for num in range(len(results)):
		print results[num]
	sys.exit(0)

	# Separate each package in the returned data.
	candidates = []
	if re.search('data\d', line):
		candidates.append(line)

	if len(candidates) == 0:
		return None

	name_list		= []
	description_list	= []
	location_list		= []
	category_list		= []
	maintainer_list		= []
	votes_list		= []

	ct = 0
	while ct < len(candidates):
		if (ct * 6) < len(candidates):
			location = location.split("Location")[0]
			category = category.split("Category")[0]
			name = name.split("Name")[0]
			votes = votes.split("NumVotes")[0]
			description = description.split("Description")[0]

#			maintainer = maintainer.split('Maintainer')[0]
			maintainer = ''

			name_list.append(name)
			description_list.append(description)
			location_list.append(location)
			category_list.append(category)
			maintainer_list.append(maintainer)
			votes_list.append(votes)
		ct = ct + 1

	return name_list, description_list, location_list, category_list, maintainer_list, votes_list


if __name__ == '__main__':
	import sys
	print aursearch(sys.argv[1], 'http://aur.archlinux.org/')
	sys.exit(0)
