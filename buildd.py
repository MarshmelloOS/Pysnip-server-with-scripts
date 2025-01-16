"""
Starts build mode for build server. Protects areas, changes team names and locks
builder team.
"""

from pyspades.common import coordinates
import commands

DONT_PROTECT = ['g7', 'g8', 'h7', ' h8']


@commands.admin
def protectall(connection):
    connection.protocol.init_protect()
    connection.send_chat('Build areas protected')
commands.add(protectall)


def apply_script(protocol, connection, config):
    class BuildProtocol(protocol):
        def __init__(self, *args, **kargs):
            protocol.__init__(self, *args, **kargs)
            self.blue_team.locked = True
            self.blue_team.name = 'Builders'
            self.green_team.name = 'Others'
            self.init_protect()

        def init_protect(self):
            self.protected = set()
            for letter in 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h':
                for num in range(8):
                    grid = letter+str(num+1)
                    if grid not in DONT_PROTECT:
                        pos = coordinates(grid)
                        self.protected.symmetric_difference_update([pos])

    return BuildProtocol, connection
