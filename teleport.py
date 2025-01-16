'''

This is an open source remake for the script hookshot.py by Mr.Morphman.
It was written completely from scratch.
Feel free to contribute!

LICENSE: BSD-3 (do what you want with it).

This version is made for PySnip.

'''




from pyspades.constants import FALL_KILL
import time
from pyspades import world
from math import sqrt
from twisted.internet import reactor
from commands import name, add, admin, alias

@admin
@name('teleportdistance')
@alias('td')
def tpd(self, value):
    try:
        self.protocol.length = int(value)
        if value == 0:
            self.send_chat('Teleport feature successfully deactivated. Congratulations, spoilsport.')
        else:
            self.send_chat('Teleport distance set to '+str(self.protocol.length))
                    
    except:
        self.send_chat("Oops! That didn't work. Try again!")


@admin
@name('teleportspeed')
@alias('ts')
def tpts(self, value):
    try:
        value=float(value)
        if value > 0:
            self.protocol.speed=1/value
            self.send_chat('Teleport speed set to '+str(value)+' blocks per second')
        elif value == 0:
            self.send_chat('To deactivate teleport, set the teleport distance to zero.')
        else:
            self.send_chat('Positive people use positive numbers.')
    except:
        self.send_chat("Oops! That didn't work. Try again!")

@admin
@name('teleportcooldown')
@alias('tc')
def tpc(self, value):
    try:
        value=float(value)
        self.protocol.cooldown = value
        self.send_chat('Teleport cooldown time set to '+str(value))
    except:
        self.send_chat("Oops! That didn't work. Try again!")

add(tpd)
add(tpts)
add(tpc)

def ff(player):
    if player.allhisplannedstuff=={}:
        player.unfallable = False

def set_pos(player, goal, pos):
    blockdistance=int(sqrt((goal[0]-pos[0])**2 + (goal[1]-pos[1])**2 + (goal[2]-pos[2])**2))
    blockdistance += 1
    teleporttime=time.time()
    player.unfallable = True
    player.makeunfallable[teleporttime]=reactor.callLater(player.protocol.speed*blockdistance+4, ff, player)
    vectorx=(goal[0]-pos[0])/blockdistance
    vectory=(goal[1]-pos[1])/blockdistance
    vectorz=(goal[2]-pos[2])/blockdistance #noclipping during flight is intended
    for i in range(1,blockdistance):
        player.allhisplannedstuff[teleporttime*i]=reactor.callLater(player.protocol.speed*(i), player.give_pos, (pos[0]+vectorx*i, pos[1]+vectory*i,pos[2]+vectorz*i), teleporttime, i)

    
    
def apply_script(protocol, connection, config):
    class teleportprotocol(protocol):
        cooldown = 8
        length = 120
        speed=0.004
        previouscooldown = cooldown
        previouslength = length
        
        def on_advance(self, *arg, **kw):
            self.previouscooldown = self.cooldown
            self.cooldown = 0 #this feature lets everyone teleport around in the end
            self.previouslength = self.length
            self.length = 300
        
        def on_map_change(self, map):
            for playerz in self.players.values():
                for allkeys in playerz.allhisplannedstuff:
                    if playerz.allhisplannedstuff[allkeys].active():
                        playerz.allhisplannedstuff[allkeys].cancel()
                playerz.allhisplannedstuff={}
                for unfallablekeys in playerz.makeunfallable:
                    if playerz.makeunfallable[unfallablekeys].active():
                        playerz.makeunfallable[unfallablekeys].cancel()
                playerz.makeunfallable={}
            self.cooldown = self.previouscooldown
            self.length = self.previouslength
            return protocol.on_map_change(self, map)

    class teleportconnection(connection):
        unfallable = False
        lastteleport = 0.0
        allhisplannedstuff = {}
        makeunfallable = {}
        
        def give_pos(player, position, teleporttime, iterator):
            if player is not None:
                try:
                    if (position[0]>=0) and (position[0]<=511) and (position[1] >=0) and (position[1]<=511) and (position[2]>-5) and (position[2]<=63):
                        player.set_location(position)
                    player.allhisplannedstuff.pop(teleporttime*iterator)
                except:
                    pass
                        
        def on_spawn(self, pos):
            self.lastteleport=0.0 #reset on start
            return connection.on_spawn(self, pos)
            
        def on_fall(self, damage):
            if self.unfallable:
                if self.allhisplannedstuff == {}:
                    self.unfallable = False
                    for unfallablekeys in self.makeunfallable:
                        if self.makeunfallable[unfallablekeys].active():
                            self.makeunfallable[unfallablekeys].cancel()
                    self.makeunfallable={}
                return False
            return connection.on_fall(self, damage)
        
        def on_kill(self, killer, type, grenade):
            for keys2 in self.allhisplannedstuff:
                if self.allhisplannedstuff[keys2].active():
                    self.allhisplannedstuff[keys2].cancel()
            self.allhisplannedstuff={}
            return connection.on_kill(self, killer, type, grenade)
        
        def on_animation_update(self, jump, crouch, sneak, sprint):
            
            if (((time.time()-self.lastteleport) >= self.protocol.cooldown) or self.invisible) and sneak == True and not self.team.other.flag.player is self and self.world_object.cast_ray(self.protocol.length) is not None:
                for unfallablekeys in self.makeunfallable:
                    if self.makeunfallable[unfallablekeys].active():
                        self.makeunfallable[unfallablekeys].cancel()
                self.makeunfallable={}
                if self.world_object.velocity.z >= 0.58 and not self.god:
                    self.kill(self, FALL_KILL)
                headpoints = world.cube_line(*(self.world_object.cast_ray(self.protocol.length)) + (self.world_object.position.get()))
                nice=False
                for headblocks in headpoints:
                    x1,y1,z1=headblocks
                    if self.protocol.map.get_solid(x1,y1,z1) == 0 and self.protocol.map.get_solid(x1,y1,z1 + 1) == 0 and self.protocol.map.get_solid(x1, y1, z1 + 2) == 0:
                        nice=True
                        set_pos(self, (x1,y1,z1+1), (self.world_object.position.get()))
                        break
                    elif self.protocol.map.get_solid(x1,y1,z1-1) == 0 and self.protocol.map.get_solid(x1,y1,z1) == 0 and self.protocol.map.get_solid(x1, y1, z1 + 1) == 0:
                        nice=True
                        set_pos(self, (x1,y1,z1), (self.world_object.position.get()))
                        break
                    elif self.protocol.map.get_solid(x1,y1,z1-2) == 0 and self.protocol.map.get_solid(x1,y1,z1-1 ) == 0 and self.protocol.map.get_solid(x1, y1, z1) == 0:
                        nice=True
                        set_pos(self, (x1,y1,z1-1), (self.world_object.position.get()))
                        break
                    elif (z1<=1) * (self.world_object.position.z<4):
                        nice=True
                        set_pos(self, (x1,y1,z1-2), (self.world_object.position.get()))
                        break
                if nice == False: #emergency case
                    x1, y1, z1 = self.world_object.cast_ray(self.protocol.length)
                    x1, y1, z1 = int(x1), int(y1), int(z1)
                    for pos in self.protocol.pos_table:
                        if self.is_location_free(x1 + pos[0], y1 + pos[1], z1 + pos[2]):
                            set_pos(self, (x1 + pos[0],y1 + pos[1],z1 + pos[2]), (self.world_object.position.get()))
                            break
                self.lastteleport=time.time()
            return connection.on_animation_update(self, jump, crouch, sneak, sprint)
        
        def on_disconnect(self):
            for allkeys in self.allhisplannedstuff:
                if self.allhisplannedstuff[allkeys].active():
                    self.allhisplannedstuff[allkeys].cancel()
            self.allhisplannedstuff={}
            for unfallablekeys in self.makeunfallable:
                if self.makeunfallable[unfallablekeys].active():
                    self.makeunfallable[unfallablekeys].cancel()
            self.makeunfallable={}
            connection.on_disconnect(self)
    return teleportprotocol, teleportconnection
