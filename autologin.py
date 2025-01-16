"""
autologin script ver0.6 by yuyasato

should make "autologinips.txt" in dist

written by json(automatic)
[<Marshmello>, <127.0.0.1>, <user_type(admin)>]
[<Grimston>, <81.157.242.28>, <user_type(admin)>]
[<IC-Liza>, <127.0.0.1>, <user_type(admin)>]

"""

from commands import add, admin, get_player, login
from pyspades.constants import *
from networkdict import NetworkDict, get_network
from paint import paintlogin
from buildtools import bulk
import sys
import os
import json


#####

KENTIKU_MODE = False		#if this is true, admin user will not need /god /dash /fly and /paint. automatic command when into server.



def apply_script(protocol,connection,config):
	class AutologinConnection(connection):

		def on_user_login(self, user_type, verbose = True):
			self.write_list(user_type)
			return connection.on_user_login(self, user_type, verbose)

		def write_list(self, post):
			self.ips = NetworkDict()
			try:
				self.ips.read_list(json.load(open('autologinips.txt', 'rb')))
			except IOError:
				print "autologinips.txt open error."
				pass

			client_ip = self.address[0]

			try:
				list = self.ips[client_ip]
				if post != list[1]:
					self.ips.remove(client_ip)
					name = self.name
					self.ips[client_ip] = (name or '(unknown)', post)			
					json.dump(self.ips.make_list(), self.open_create('autologinips.txt', 'wb'), indent = 4)
					self.send_chat("Added your ip in Autologin list. You can use autologin as %s after next time."% post)
				else:
					return

			except KeyError:
				name = self.name
				self.ips[client_ip] = (name or '(unknown)', post)			
				json.dump(self.ips.make_list(), self.open_create('autologinips.txt', 'wb'), indent = 4)
				self.send_chat("Added your ip in Autologin list. You can use autologin as %s after next time."% post)


		def on_spawn(self, pos):
			if self.user_types:
				return connection.on_spawn(self, pos)
			else:
				self.ips = NetworkDict()
				try:
					self.ips.read_list(json.load(open('autologinips.txt', 'rb')))
				except IOError:
					print "autologinips.txt open error."
					pass

				protocol = self.protocol
				client_ip = self.address[0]
				try:
					list = self.ips[client_ip]
					name = list[0]
					post = list[1]

					self.passwords = config.get('passwords', {})

					pas= self.passwords.get(post, [])
					if pas==[]:
						print "password is None"
						return connection.on_spawn(self, pos)

					self.send_chat("Autologin successful.")
					login(self,pas[0])
					print name +" ("+ client_ip +") was auto loginned as " + post + "."

					if post=="admin" and KENTIKU_MODE:
						bulk(self)
						paintlogin(self)
					return connection.on_spawn(self, pos)
				except KeyError:
					pass
				return connection.on_spawn(self, pos)

		def create_path(self,path):
		    if path:
		        try:
		            os.makedirs(path)
		        except OSError:
		            pass

		def create_filename_path(self,path):
		    self.create_path(os.path.dirname(path))

		def open_create(self,filename, mode):
		    self.create_filename_path(filename)
		    return open(filename, mode)

	
	return protocol,AutologinConnection
