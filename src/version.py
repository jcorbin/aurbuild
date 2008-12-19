#
#   version.py
#
#   Copyright (C) 2006-2007 by Tyler Gates <TGates81@gmail.com>
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

import re

class vercmp:
	def strip_release(self, ver):
		"""
		Separate out the pkgrel number from a package version.

		Return two strings:
			ver: the package version
			rel: the PKGBUILD pkgrel
		"""

		rerel = '-[0-9]*$'
		rel = 0
		if re.search(rerel, ver):
			tmp_ver = re.sub(rerel, '', ver)
			rel = re.sub(tmp_ver, '', ver)
			# strip out the "-" in rel 
			rel = re.sub('-', '', rel)
			if rel == '': rel = 0
			ver = tmp_ver

		return ver, rel
	
		
	def vercmp(self, ver1, ver2):
		"""
		Compare two version numbers.
		
		Return an integer:
			-1: ver1 is an earlier release
			 0: ver1 and ver2 are the same
			 1: ver1 is a later release
		"""

		# remove release number and store for later use
		ver1, rel1 = self.strip_release(ver1)
		ver2, rel2 = self.strip_release(ver2)

		# split at "." and "-"
		ver1 = re.split('[\.,-]', ver1)
		ver2 = re.split('[\.,-]', ver2)

		def remove_empty(ver):
			i = 0
			while i < len(ver):
				if ver[i] == '': 
					ver.remove(ver[i])
					i -= 1
				i += 1
			return ver

		# remove empty splits -for situations where our split points ("." and "-") are together
		ver1 = remove_empty(ver1)
		ver2 = remove_empty(ver2)

		def pad(v1, v2):
			v1_len = len(v1)
			v2_len = len(v2)
			if v1_len > v2_len:
				for pad in range(v1_len - v2_len):
					v2.extend('0')
			elif v2_len > v1_len:
				for pad in range(v2_len - v1_len):
					v1.extend('0')
			return v1, v2

		# pad with zeros
		ver1, ver2 = pad(ver1, ver2)

		alphas = '[a-zA-Z]+'
		nums = '[0-9]+'
		notalphanum = '[^0-9a-zA-Z]+'
		alphanum = '[0-9a-zA-Z]+'

		def alnum_split(ver):
			alver = re.findall(alphas, ver)
			numver = re.findall(nums, ver)

			if alver == [] and numver == []:
				return ver
			elif alver == [] and numver != []:
				return numver
			elif alver != [] and numver == []:
				return alver
			else:
				# both must have matches, recombine using original ver order:

				# find which list starts with the original string
				if re.match(alver[0], ver): 
					starter = alver
					follower = numver
				else:
					starter = numver
					follower = alver

				# recombine
				len_starter = len(starter)
				len_follower = len(follower)
				itr_num = max(len_starter, len_follower)
				recombined = []
				for i in range(itr_num):
					if i <= len_starter-1: recombined.append(starter[i])
					if i <= len_follower-1: recombined.append(follower[i])

				return recombined

		for num in range(len(ver1)):
			# strip out special characters
			ver1[num] = re.sub(notalphanum, '', ver1[num])
			ver2[num] = re.sub(notalphanum, '', ver2[num])

			# if any alpha is found, we must go through and split at alpha and digit and compare
			if re.search(alphas, ver1[num]) or re.search(alphas, ver2[num]):
				tmpver1 = alnum_split(ver1[num])
				tmpver2 = alnum_split(ver2[num])
				tmpver1, tmpver2 = pad(tmpver1, tmpver2)
				for i in range(len(tmpver1)):
					if tmpver1[i].isdigit() and tmpver2[i].isdigit():
						tmpver1[i] = int(tmpver1[i])
						tmpver2[i] = int(tmpver2[i])
						
					elif tmpver1[i].isalpha() and tmpver2[i].isalpha():
						# nothing more to do, pass
						pass
					
					elif tmpver1[i].isdigit() and tmpver2[i].isalpha():
						tmpver1[i] = int(tmpver1[i]) + 1
						tmpver2[i] = 0

					elif tmpver1[i].isalpha() and tmpver2[i].isdigit():
						tmpver2[i] = int(tmpver2[i]) + 1
						tmpver1[i] = 0

					# now we can compare them
					if tmpver1[i] > tmpver2[i]: return 1
					elif tmpver1[i] < tmpver2[i]: return -1
			# must be only digits, compare them
			else:
				if int(ver1[num]) > int(ver2[num]): return 1
				elif int(ver1[num]) < int(ver2[num]): return -1

		# compare release if we have gotten this far
		if int(rel1) > int(rel2): return 1
		elif int(rel1) < int(rel2): return -1

		# everthing must be equal, return 0
		return 0
