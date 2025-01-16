"""
Really simple viewing command to stay dead
and thereby use the team spectating you get there
thepolm3
StarDust requested
"""
from commands import add

def ovl(connection):
    connection.ovl=not connection.ovl
    if connection.ovl: connection.kill()
    else: connection.spawn()
    return "OVL %sactivated" %(["de",""][connection.ovl])

add(ovl)
def apply_script(protocol,connection,config):
    class OVLConnection(connection):
        ovl=False
        def get_respawn_time(self):
            if self.ovl:
                return -1
            else:
                return connection.get_respawn_time(self)

        def respawn(self):
            if not self.ovl:
                connection.respawn(self)
    return protocol,OVLConnection
