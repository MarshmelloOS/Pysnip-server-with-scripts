#Where am I script by Kuma
#Version 2.0

from commands import alias, add, name

@alias('wai')
def whereami(connection):
    protocol = connection.protocol
    if connection in protocol.players:
        player = connection
    else:
        raise ValueError()
    player.whereami = not player.whereami

    message = 'now in where am I mode' if player.whereami else 'no longer in where am I mode'
    player.send_chat("You are {0}".format(message))

add(whereami)    

def apply_script(protocol, connection, config):
    class whereConnection(connection):
        whereami = False
        def on_block_destroy(self, x, y, z, mode):
            if self.whereami:
                self.send_chat("X = {0}, Y = {1}, Z = {2}".format(x, y, z))
                return False
            else:
                return connection.on_block_destroy(self, x, y, z, mode)
    return protocol, whereConnection