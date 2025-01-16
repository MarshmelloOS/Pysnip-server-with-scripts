import os
from pyspades.constants import *

def apply_script(protocol, connection, config):
	class DoorBellConnection(connection):
	
		def on_connect(self):
			print("\007")
			return connection.on_connect(self)
			
	return protocol, DoorBellConnection
