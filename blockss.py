from commands import add, name

@name('blocks')
def toggle_Blocks_mode(connection):
    protocol = connection.protocol
    if connection in protocol.players:
        connection.Blocks_mode = not connection.Blocks_mode
        return "You are {} blocks mode.".format(["out of", "now in"][int(connection.Blocks_mode)])

add(toggle_blocks_mode)

def apply_script(protocol, connection, config):

    class blockConnection(connection):
        Blocks_mode = false
       
        def on_block_build(self, x, y, z):
            if self.Blocks_mode:
                self.refill()
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if self.Blocks_mode:
                self.refill()
            return connection.on_line_build(self, points)

    return protocol, blockConnection