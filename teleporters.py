"""
Teleporters
by Desert Storm
teleport from one location to another(think halo or portal)
"""

###Summary###
#this allows the server admin to declare locations in the map config file
#there can be single, multi, one-way portal links

#the algorithim I use seaches the map config for the first location that matches
#the players coordinates. if it finds a match is will then pick a random tuple
#or int from the same group this(50,14,30) is a tuple and this(4) is an int
#the integers are used to make one-way links

###Important###
#you may modify this file, however you still have to leave the 'by Desert Storm'
#part at the top of the file AND
#give credit to me if you post this elsewhere

###Notes###
#define the location so that there is one block of air between the location
#and the ground

#this does NOT check for anything lower than 2 or higher than 60

#for the one-way link the '#' is any existing index point in the 'otps'
#decleration

#you can have no less than two declarations in a group otherwise this will
#raise an Exception

#having dipped my spoon in to assembly language I know how important
#optimization is, so I have tried to make this use as little memory as I can
#with my current knowledge of python

###Examples###
#your config file can be any combination of the following

#map config file look:
#name ***
#author ***
#version ***
#description ***
#extensions = {'tps':[(())],
#              'otps':[()]
#             }

#Normal link:
#extensions = {
#             'tps':[((x1,y1,z1),(x2,y2,z2))]
#             }

#multiple groups:
#extensions = {
#             'tps':[((x1,y1,z1),(x2,y2,z2)),((x3,y3,z3),(x4,y4,z4))]
#             }

#multi link:
#extensions = {
#             'tps':[((x1,y1,z1),(x2,y2,z2),(x3,y3,z3))]
#             }

#one-way link:
#extensions = {
#             'tps':[((x1,y1,z1),(#))]
#             'otps':[(x2,y2,z2)]
#             }

from random import choice
from commands import add, admin, alias

def Teleporters(Exception):
    pass

TPI = 'Teleporter index set to {number}'

@admin
def tpindex(connection, index=None):
    connection.tpindex = int(index)
    return TPI.format(number=index)

add(tpindex)

def apply_script(protocol, connection, config):

    class tpc(connection):

        def coord_check(self, pos):
            p = self.protocol.map_info.extensions
            newpos = pos
            if p.has_key('tps'):
                pp = p['tps']
                for i in xrange(len(pp)):
                    if pos in pp[i]:
                        if self.tpindex != None:
                            if self.tpindex <= len(pp[i]):
                                newpos = pp[i][self.tpindex]
                                if type(newpos)==int:
                                    if p.has_key('otps'):
                                        ppp = p['otps']
                                        try:
                                            newpos = ppp[newpos]
                                        except IndexError:
                                            Teleporters("There is no index %d in 'otps'" % newpos)
                                            newpos = pos
                                    else:
                                        raise Teleporters("There is no otps decleration in the map txt")
                                        newpos = pos
                            self.tpindex = None
                            break
                        if len(pp[i])>2:
                            test = True
                            testnum = 0
                            while test:
                                newpos = choice(pp[i])
                                if type(newpos)==int:
                                    if p.has_key('otps'):
                                        ppp = p['otps']
                                        try:
                                            newpos = ppp[newpos]
                                        except IndexError:
                                            raise Teleporters("There is no index %d in 'otps'" % newpos)
                                            newpos = pos
                                            test = False
                                    else:
                                        raise Teleporters("There is no 'otps' decleration in the map config file")
                                if newpos!=pos:
                                    test = False
                                if testnum==7:
                                    test = False
                                testnum += 1
                            break
                        elif len(pp[i])>1:
                            if pp[i].index(pos)==0:
                                newpos = pp[i][1]
                                if type(newpos)==int:
                                    if p.has_key('otps'):
                                        ppp = p['otps']
                                        try:
                                            newpos = ppp[newpos]
                                        except IndexError:
                                            raise Teleporters('There is no index %d in otps' % newpos)
                                            newpos = pos
                            else:
                                newpos = pp[i][0]
                                if type(newpos)==int:
                                    if p.has_key('otps'):
                                        ppp = p['otps']
                                        try:
                                            newpos = ppp[newpos]
                                        except IndexError:
                                            raise Teleporters('There is no index %d in otps' % newpos)
                                            newpos = pos
                            break
                        else:
                            raise Teleporters("There is less than two locations in group %d" % i)
                            break
            return newpos
        
        def on_position_update(self):
            x, y, z = self.get_location()
            if self.world_object.crouch:
                pos = int(x), int(y), int(z)
            else:
                pos = int(x), int(y), int(z+1)
            if pos[2]<60 or pos[2]>2:
                if pos != self.old_pos:
                    newpos = self.coord_check(pos)
                    if newpos!=pos:
                        self.set_location((newpos[0],newpos[1],newpos[2]-1))
                    self.old_pos = newpos
            return connection.on_position_update(self)

        def on_spawn_location(self, pos):
            self.old_pos = pos
            return connection.on_spawn_location(self, pos)

        def on_join(self):
            self.tpindex = None
            self.old_pos = None
            return connection.on_join(self)

    return protocol, tpc
