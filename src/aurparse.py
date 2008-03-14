#
#   aurparse.py
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

import re, os, sys, urllib

aururl = 'http://aur.archlinux.org/'
search_url = aururl + 'packages.php?K='

# this looks a little strange but we need to access each of these functions (except aursearch) and query the server only once, hence the
# manual 'raw_text' parameters which is currently obtained from raw_pkg_query().

def raw_pkg_query(keyword):
	f = urllib.urlopen(search_url+keyword+'&PP=100')
	lines = f.readlines()
	return lines

def pkg_main_url(pkg):
	raw_text = []

	try:
		raw_text = raw_pkg_query(pkg)
	except Exception, e:
		print >>sys.stderr.write('\ncould not retrieve needed data' +
			'from aur: ' + str(e))
		cleanup()
		sys.exit(1)


        url = '' 
        for line in raw_text:
                if 'packages.php?ID' in line and '>'+pkg+' ' in line:
                        url = line.split("ID=", 1)[1]
                        url = url.split("'>")[0]
			url = aururl + "packages.php?ID=" + url
			break
	return url

def pkg_tarball_url(raw_text):
	url = ''
	for line in raw_text:
		if '\'>Tarball</a>' in line:
			url = line.split("<a href='")[1]
			url = url.split("'>Tarball")[0]
			url = aururl + url
	return url


def aursearch(keyword):
	""" search(keyword)
	search http://aur.archlinux.org/ search engine to find keyword and return info."""

	f = raw_pkg_query(keyword)

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
	print aursearch(sys.argv[1])
	sys.exit(0)
