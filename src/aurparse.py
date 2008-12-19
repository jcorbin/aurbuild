#
#   aurparse.py
#
#   Copyright (C) 2005-2007 by Tyler Gates <TGates81@gmail.com>
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
The format of the 'site' argument must be protocol://domain/.
ex: http://aur.archlinux.org/
The trailing slash is important
"""

# this looks a little strange but we need to access each of these
# functions (except aursearch) and query the server only once,
# hence the manual 'raw_text' parameters which is currentlyi
# obtained from raw_pkg_query().

def raw_pkg_query(keyword, site):
	search_url = site + 'packages.php?K='
	f = urllib.urlopen(search_url+keyword+'&PP=100')
	lines = f.readlines()
	return lines

def pkg_main_url(pkg, site):
	raw_text = []

	try:
		raw_text = raw_pkg_query(pkg, site)
	except Exception, e:
		print >>sys.stderr.write(
			'Could not retrieve needed data from ' + site)
		raise


	url = ''
	for line in raw_text:
		if 'packages.php?ID' in line and '>'+pkg+' ' in line:
			url = line.split("ID=", 1)[1]
			url = url.split("'>")[0]
			url = site + "packages.php?ID=" + url
			break

	return url


def pkg_tarball_url(raw_text, site):
	url = ''
	for line in raw_text:
		if '\'>Tarball</a>' in line:
			url = line.split("<a href='")[1]
			url = url.split("'>Tarball")[0]
			url = site + url
	return url

def aursearch(keyword, site):
	"""
	Gets and parses the output from the site's search page.

	Returns a set of arrays that contain the package info in the order of:
	names, descriptions, locations, categories, maintainers, and votes.
	"""

	f = raw_pkg_query(keyword, site)

	candidates = []
	for line in f:
		if re.search('data\d', line):
			candidates.append(line)

	if len(candidates) == 0:
		return None, None, None, None, None, None

	name_list		= []
	description_list	= []
	location_list		= []
	category_list		= []
	maintainer_list		= []
	votes_list		= []

	ct=0
	while ct<len(candidates):
		if ct*6<len(candidates):
			location = candidates[ct * 6].split("class='blue'>")[1]
			location = location.split("</span")[0]
			category = candidates[(ct * 6) + 1].split("class='blue'>")[1]
			category = category.split("</span")[0]
			color="'black'"
			name = candidates[(ct * 6) + 2].split("class=" + color + ">")[1]
			name = name.split("</span></a>")[0]
			votes = candidates[(ct * 6) + 3].split("&nbsp;&nbsp;&nbsp;")[1]
			votes = votes.split("</span")[0]
			description = candidates[(ct * 6) + 4].split("class='blue'>")[1]
			description = description.split("</span>")[0]
			maintainer = candidates[(ct * 6) +5]
			if re.search("'>orphan", maintainer):
				maintainer = 'ORPHANED'
			else:
				maintainer = maintainer.split('</a>')[0]
				maintainer = maintainer.rsplit('>', 1)[1]

			name_list.append(name)
			description_list.append(description)
			location_list.append(location)
			category_list.append(category)
			maintainer_list.append(maintainer)
			votes_list.append(votes)
		ct=ct+1

	return name_list, description_list, location_list, category_list, maintainer_list, votes_list


if __name__ == '__main__':
	import sys
	print aursearch(sys.argv[1], 'http://aur.archlinux.org/')
	sys.exit(0)
