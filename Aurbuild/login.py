#
#   login.py
#
#   Copyright (C) 2006-2007 by Tyler Gates <TGates81@gmail.com>
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

import cookielib, os, urllib2


class LoginError(Exception):
	# base exception
	pass

class CookieError(LoginError):
	# general cookie errors
	pass

class AuthenticationError(LoginError):
	# general login errors
	pass

class ActionError(LoginError):
	# general action errors
	pass

class TargetError(LoginError):
	# general target errors
	pass

class aurlogin:
	def __init__(self):
		self.cookie_jar = cookielib.LWPCookieJar()
		self.aursite	= 'http://aur.archlinux.org/'
		self.headers	= {'User-agent': 'Mozilla/4.0 (compatible; Linux)'}

	def get_cookie(self, cookiefile):
		""" get a cookie from the main site and save it to cookiefile """
		
		# create dirname of cookie file if not found
		cookie_dir = os.path.dirname(cookiefile)
		if not os.path.isdir(cookie_dir):
			try:
				os.makedirs(cookie_dir)
			except Exception, e:
				raise CookieError, 'could not create cookie directory `'+cookie_dir+'\'. '+str(e)
		
		req = urllib2.Request(self.aursite, None, self.headers)
		handle = urllib2.urlopen(req)
		# save the cookie
		self.cookie_jar.save(cookiefile)

	def logout(self):
		""" logout of the main site """
		
		try:
			req = urllib2.Request(self.logout_url, None, self.headers)
			handle = urllib2.urlopen(req)
		except:
			# fuck it
			pass

	def login(self, username, password, cookiefile):
		""" login to the main site """
	
		# set the language to english so we can parse for expected response words
		# this will not permanently set the user's default language to english
		login_url	= self.aursite+'index.php?setlang=en&user='+username+'&pass='+password
		
		# get a cookie
		if not os.path.isfile(cookiefile): self.get_cookie(cookiefile)
		
		# build an opener for the cookie
		self.cookie_jar.load(cookiefile)
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
		urllib2.install_opener(self.opener)

		# login request
		req = urllib2.Request(login_url, None, self.headers)
		handle = urllib2.urlopen(req)
		
		# checked that we are logged in
		logged_in = 0
		for line in handle:
			if 'Logged-in as:' in line: 
				logged_in = 1
				break
		if not logged_in: 
			raise AuthenticationError, 'invalid username or password'

	def vote(self, username, password, cookiefile, pkgname):
		""" vote for pkgname and return 2 if already voted """

		search_url = self.aursite+'packages.php?K='+pkgname

		# login
		self.login(username, password, cookiefile)
		
		# query for pkgname
		req = urllib2.Request(search_url, None, self.headers)
		handle = urllib2.urlopen(req)
		lines = handle.readlines()
		valid_pkg = 0
		for line in lines:
			if '>'+pkgname+' ' in line:
				valid_pkg = 1
				# get the ID
				id = line.split('ID=')[1]
				id = id.split('&')[0]
				# the next 2 lines are voted status, get that
				cur = int(lines.index(line))
				voted = lines[cur+2]
				if not 'Yes' in voted:
					# haven't voted yet, do it
					vote_url = self.aursite+'packages.php?IDs['+id+']&do_Vote'
					req = urllib2.Request(vote_url, None, self.headers)
					handle = urllib2.urlopen(req)

					# confirm
					confirmed = 0
					for l in handle:
						if 'votes have been cast' in l: 
							confirmed = 1
							self.logout()
							break
					if not confirmed:
						self.logout()
						raise ActionError, 'action confirmation indicates failure'
				else: 
					# return 2 because the action has already been performed
					self.logout()
					return 2
				self.logout()
				return
		if not valid_pkg: 
			self.logout()
			raise TargetError, '`'+pkgname+'\' not found on host'


	def unvote(self, username, password, cookiefile, pkgname):
		""" un-vote for pkgname and return 2 if not voted """

		search_url = self.aursite+'packages.php?K='+pkgname
		
		# login
		self.login(username, password, cookiefile)

		# query for pkgname
		req = urllib2.Request(search_url, None, self.headers)
		handle = urllib2.urlopen(req)
		lines = handle.readlines()
		valid_pkg = 0
		for line in lines:
			if '>'+pkgname+' ' in line and 'packages.php?' in line:
				valid_pkg = 1
				# get the ID
				id = line.split('ID=')[1]
				id = id.split('&')[0]
				# the next 2 lines are voted status, get that
				cur = int(lines.index(line))
				voted = lines[cur+2]
				if 'Yes' in voted:
					# have voted, unvote
					voted_url = self.aursite+'packages.php?IDs['+id+']&do_UnVote'
					req = urllib2.Request(voted_url, None, self.headers)
					handle = urllib2.urlopen(req)

					# confirm
					confirmed = 0
					for l in handle:
						if 'have been removed' in l: 
							confirmed = 1
							self.logout()
							break
					if not confirmed:
						self.logout()
						raise ActionError, 'action confirmation indicates failure'
				else: 
					# return 2 because the action has already been performed
					self.logout()
					return 2
				self.logout()
				return
		if not valid_pkg: 
			self.logout()
			raise TargetError, '`'+pkgname+'\' not found on host'

