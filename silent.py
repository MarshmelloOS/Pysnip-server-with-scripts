"""
Allows using commands without being shown to the game or irc. Simply add "silent" to the end of any other valid command.
For example "\login password silent" will log a player in without notifying other users. Any messages that would be
send globally are send to the user of the command as "silently: message". Any message that would be sent to another user
is send to the user of send as "silently to: message".
"""


def apply_script(protocol, connection, config):
    class CommandConnection(connection):
        def on_command(self, command, parameters):
            if len(parameters) == 0:
                connection.on_command(self, command, parameters)
                return
            if parameters[-1].lower() == 'silent':
                if 'silent' not in self.rights:
                    self.send_chat("You can't do that silently")
                    log_message = '<%s> /%s %s' % (self.name, command, ' '.join(parameters))
                    log_message += ' -> %s' % 'No Permission for silent'
                    print(log_message.encode('ascii', 'replace'))
                    return
                parameters.pop(-1)

                # Backup old methods
                old_connection_send = connection.send_chat
                old_protocol_send = self.protocol.send_chat
                old_irc_say = self.protocol.irc_say

                # Set new methods
                connection.send_chat = lambda conn, msg, **kwargs:  \
                    self.send_chat('Silently to ' + conn.name + ': ' + msg)
                self.protocol.send_chat = lambda msg, **kwargs: self.send_chat('Silently: ' + msg)
                self.protocol.irc_say = lambda msg: None
                self.send_chat = old_connection_send

                connection.on_command(self, command, parameters)

                # Reset methods
                del self.send_chat
                self.protocol.send_chat = old_protocol_send
                connection.send_chat = old_connection_send
                self.protocol.irc_say = old_irc_say
            else:
                connection.on_command(self, command, parameters)

    return protocol, CommandConnection
