"""
Lets non-admin commands be specified explicitly in the config. No other commands are allowed for regular users

Config format:
############################################

    "defaultcommands": ["command1","command2"]
	
###########################################
"""

import commands
from commands import InvalidPlayer, InvalidTeam


def handle_command(connection, command, parameters):
    command = command.lower()
    try:
        command = commands.aliases[command]
    except KeyError:
        pass
    try:
        command_func = commands.commands[command]
    except KeyError:
        return  # 'Invalid command'
    try:
        if (command_func.func_name not in connection.protocol.defaultcommands and
                command_func.func_name not in connection.rights):
            return "You can't use this command"
        return command_func(connection, *parameters)
    except KeyError:
        return  # 'Invalid command'
    except TypeError:
        return 'Invalid number of arguments for %s' % command
    except InvalidPlayer:
        return 'No such player'
    except InvalidTeam:
        return 'Invalid team specifier'
    except ValueError:
        return 'Invalid parameters'


def apply_script(protocol, connection, config):

    class CommandConnection(connection):
        def on_command(self, command, parameters):
            result = handle_command(self, command, parameters)
            if result is False:
                parameters = ['***'] * len(parameters)
            log_message = '<%s> /%s %s' % (self.name, command, ' '.join(parameters))
            if result:
                log_message += ' -> %s' % result
                self.send_chat(result)
            print(log_message.encode('ascii', 'replace'))

    class CommandProtocol(protocol):
        def __init__(self, *args, **kwargs):
            self.defaultcommands = config.get('defaultcommands', {})
            protocol.__init__(self, *args, **kwargs)

    return CommandProtocol, CommandConnection
