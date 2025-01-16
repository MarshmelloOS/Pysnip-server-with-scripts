#Script writted by MegaStar.
#You can add a nick to a list to receive autoban.
#Example "/nameban ImNockHacker".
#More information here: http://aloha.pk/index.php?topic=10344.0
#The ban duration is 10080 (1 week) you can change it.
#Edited -caprex- 03/18/18
#Last edit 3/06/18

from pyspades.constants import *
from commands import add, admin
from twisted.internet import reactor

DEFAULT_BAN_DURATION = 1 # default duration (1 week)
FILE_NAME = "nameban.txt"  # change this if you want an specific file name

@admin
def nameban(connection,*name):
    if len(name) == 0:
        return "you need to specify a name: /nameban <nick>"
    name = ' '.join(name)
    with open(FILE_NAME, mode="r") as s:
        nicks = [nick.lower() for nick in s.read().splitlines()]
        for nick in nicks:
            if nick[0] == '*' and nick[len(nick)-1] == '*':
                if name[0] == '*' and name[len(name)-1] == '*':
                    if name[1:len(name)-1].lower() == nick[1:len(nick)-1].lower():
                        return "the name already exist."
                elif name.lower() == nick[1:len(nick)-1].lower():
                    return "the name already exist."
            elif name[0] == '*' and name[len(name)-1] == '*':
                if name[1:len(name)-1].lower() == nick.lower():
                    return "the name already exist."
            elif name.lower() == nick.lower():
                return "the name already exist."

        with open(FILE_NAME, mode="a") as w:
            w.write("{}\n".format(name))
            return "NameBan: Saved {} to {}".format(name, FILE_NAME)

@admin
def namebanlist(connection):
    with open(FILE_NAME, mode="r") as s:
        nicks = [nick for nick in s.read().splitlines()]
        for x in range(len(nicks)):
            ID = "ID: {} | nick: {}".format(x+1,nicks[x])
            reactor.callLater(x+1,connection.send_chat,ID)


@admin
def delnameban(connection,id = None):
    if id is None:
        return "You need to specify the ID of the nameban"
    id = int(id)
    try:
        with open(FILE_NAME, mode="r") as s:
            nicks = [nick for nick in s.readlines()]
            name_nb = nicks[id-1]
            del(nicks[id-1])
            nicks_list = ''.join(nicks)
            with open(FILE_NAME, mode ="w") as f:
                f.write(nicks_list)
            return "Nameban: %s | ID: %s has just been successfully removed." % (name_nb[0:len(name_nb)-1],str(id))
    except IndexError:
        return "The ID: %s was not found." %str(id)

add(delnameban)
add(namebanlist)
add(nameban)

def apply_script(protocol, connection, config):

    class NamebanConnection(connection):

        def on_login(self,name):
            current_name = self.name
            with open(FILE_NAME) as f:
                nicks = [nick for nick in f.read().splitlines()]
                for nick in nicks:
                    if nick[0] == '*' and nick[len(nick)-1] == '*':
                        if nick[1:len(nick)-1].lower() in current_name.lower():
                           reactor.callLater(0.5, self.kick, 'nameban detected')
                           break
                    elif current_name == nick:
		        reactor.callLater(0.5,self.ban,'nameban detected',DEFAULT_BAN_DURATION)

            return connection.on_login(self,name)

    return protocol, NamebanConnection
