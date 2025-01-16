'''
#-------------------------------------------------------------------------------
# Name:        alternatelogin.py
#
# Author:      TheLoneMilkMan
#-------------------------------------------------------------------------------

Allows alternate way of doing logins in config. Each user gets their own
passowrd and can then be added to a usergroup. Each usergroup's rights are
defined in "rights", except for admin. The admin group gets every command as
usual. Use modified passreload.py script to work with this format.

Config format:
############################################
    "users": {
    	"user1" : "password1",
    	"user2" : "password2",
        "user3" : "password3"
    },
    "usergroups": {
    	"admin": ["user1","user2"],
    	"mod": ["user3"]
    },
    "rights" : {
        "mod" : ["command1", "command2"]
    },
###########################################
'''

from commands import add, get_player
import commands

def login(connection, password):
    """
    Login as a user type
    """
    if connection.username:
        return "You're already logged in as %s" % connection.username
    if connection not in connection.protocol.players:
        raise KeyError()
    for username, passwd in connection.protocol.users.iteritems():
        if password == passwd:
            connection.username = username
            return connection.on_user_login(username, True)
    if connection.login_retries is None:
        connection.login_retries = connection.protocol.login_retries - 1
    else:
        connection.login_retries -= 1
    if not connection.login_retries:
        connection.kick('Ran out of login attempts')
        return
    return 'Invalid password - you have %s tries left' % (
        connection.login_retries)
add(login)

def whois(connection, player):
    player = get_player(connection.protocol, player)
    username = player.username
    if username == None:
        message = ' is not logged in.'
    else:
        message = ' is logged in as ' + username
    return player.name + message
add(whois)

def apply_script(protocol, connection, config):

    class UserConnection(connection):
        username = None
        def on_user_login(self, username, verbose = True):
            types = []
            for user_group, names in self.protocol.usergroups.iteritems():
                if username in names:
                    types.append(user_group)
                    self.user_types.add(user_group)
                    if user_group == 'admin':
                        self.admin = True
                        self.speedhack_detect = False
                    rights = set(commands.rights.get(user_group, ()))
                    self.rights.update(rights)
            if verbose:
                message = ' logged in as %s' % (username)
                groups = ','.join(types)
                self.send_chat('You' + message)
                self.send_chat('You are in usergroups: ' + groups)
                self.protocol.irc_say("* " + self.name + message)

    class UserProtocol(protocol):
        def __init__(self,*args,**kwargs):
            self.usergroups = config.get('usergroups', {})
            self.users = config.get('users', {})
            protocol.__init__(self,*args,**kwargs)

    return UserProtocol, UserConnection