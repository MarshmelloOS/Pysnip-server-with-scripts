#script written by MegaStar 24/04/18
#comandos: </ncheck (nick)> </ipcheck (ip)>
#/ncheck: te devuelve una lista con todas las IP que uso el nick que pusiste. 
#/ipcheck: te devuelve una lista con todos los nicks que uso la IP que pusiste.
#porfavor no eliminar la linea "#SaveData #DontDeleteThisLine" del archivo datasave.txt.

#commands: </ncheck (nick)> </ipcheck (ip)>
#/ncheck: returns a list with all the IPs that use the nick that you put.
#/ipcheck: returns a list with all the nicks that use the IP that you put.
#please do not delete the line "#SaveData #DontDeleteThisLine" from the datasave.txt file.

from pyspades.constants import *
from commands import add, admin


@admin
def ncheck(connection,*nick):
    nk = ' '.join(nick[:])
    recdatos = []
    with open("datasave.txt","r") as db:
        for dates in db:
            dat = dates.split()
            pos = dat.index("|")
        
            newip = ' '.join(dat[pos+1:])
            newnick = ' '.join(dat[:pos])
            if nk == newnick:
                    recdatos.append(newip)           
    if len(recdatos) > 0:
        new = ' ,'.join(recdatos)       
        return "these IP's were found: %s"%new
        del(recdatos) 
    else:
        return "no results were found with the nick: %s" %nick
       
add(ncheck)
    
@admin
def ipcheck(connection,ip):
    ipc = str(ip)
    recdatos = []
    with open("datasave.txt","r") as db:
        for dates in db:
            dat = dates.split()             
            pos = dat.index("|")
            newip = ' '.join(dat[pos+1:])
            newnick = ' '.join(dat[:pos])
            if ipc == newip:
                recdatos.append(newnick)
    if len(recdatos) > 0:
        new = ' ,'.join(recdatos)
        return "these nick's were found: %s"%new
        del(recdatos) 
    else:
        return "no results were found with the IP: %s" %ipc
        
add(ipcheck) 


def apply_script(protocol, connection, config):
    class ToolcheckConnection(connection):
    
        def on_login(self, name):
            nick = str(self.name)
            ip = str(self.address[0])
            look = str("|")
            with open("datasave.txt","r") as db:
                for x in db:
                    new = x.split()                              
                    pos = new.index("|")
                    newnick = ' '.join(new[:pos])
		    newip = ' '.join(new[pos+1:])
                    if nick == newnick and ip == newip:
                        break
                if nick != newnick or ip != newip:
                    with open("datasave.txt","a") as db:
                        db.write('\n'+nick+' '+look+' '+ip)
            return connection.on_login(self, name) 
    
    return protocol, ToolcheckConnection           