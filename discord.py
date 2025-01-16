"""
Gives a specified amount of medkits on spawn

Author: Booboorocks998
Maintainer: mat^2
"""

import commands
from pyspades.constants import *
DISCORD_INVITE_LINK = "https://discord.com/invite/qEz5qdK9NC"

def apply_script(protocol, connection, config):
    class linesConnection(connection):
        def on_chat(self, message, client_id, channel):
            if message.startswith('/discord'):
                self.send_chat("Join our Discord server: {}".format(DISCORD_INVITE_LINK))
            else:
                return connection.on_chat(self, message, client_id, channel)
            return False

    return protocol, linesConnection
