from pyspades.server import block_action
from twisted.internet import reactor
from pyspades.constants import *
from piqueserver.commands import *

def add_block(prt,id,x,y,z,color):
 map=prt.map
 map.set_point(x,y,z,color)
 block_action.x=x
 block_action.y=y
 block_action.z=z
 block_action.player_id=id
 block_action.value=BUILD_BLOCK
 prt.send_contained(block_action,save=True)

@alias('.')
@name('bulk')
@admin
def bulk(connection):
 connection.fly=True
 connection.god=True
 connection.dash=True
 connection.send_chat("You entered GOD FLY DASH MODE ! ")
add(bulk)

@admin
def box(connection):
 connection.box=1
 connection.pole=False
 connection.send_chat("Hit 2 blocks to determine the region to make box.")
add(box)

@alias('po')
@name('pole') 
@admin  
def pole(*arguments):
 connection=arguments[0]
 length=arguments[1]
 connection.pole=True
 connection.box=0
 connection.polelength=int(length)
 connection.send_chat("Place a block to build a pole.")
add(pole)

@admin
def posy(*arguments):
 connection=arguments[0]
 if connection.posy:
  connection.posy=False
  connection.send_chat("point simmetry building is no longer enabled.")
 else:
  connection.pox=int(arguments[1])
  connection.poy=int(arguments[2])
  connection.posy=True
  connection.send_chat("point simmetry building has been enabled.")
add(posy)

@alias('d')
@name('dash')
def dash(connection):
 if connection.dash:
  connection.dash=False
  connection.send_chat("You're no longer dashing.")
 else:
  connection.dash=True
  connection.send_chat("You're dashing now.")
add(dash)

def dashmove(connection,pos,ori):
 for counter in range(16):
  pos.x+=ori[0]*2
  pos.y+=ori[1]*2
  pos.z+=ori[2]*2
  if (connection.protocol.map.get_solid(pos.x,pos.y,pos.z) or connection.protocol.map.get_solid(pos.x,pos.y,pos.z+1) or connection.protocol.map.get_solid(pos.x,pos.y,pos.z+2)):
   return
  else: reactor.callLater(0.05*counter,connection.set_location,(pos.x,pos.y,pos.z)) 

def apply_script(protocol,connection,config):
 class BTconnection(connection):
  pole=False
  polelength=0
  box=0
  boxpr=[0,0,0]
  posy=False
  pox=0
  poy=0
  dash=False
  def on_block_build_attempt(self,x,y,z):
   if self.pole:
    xh=0
    yh=0
    zh=0
    px,py,pz=self.world_object.cast_ray(16)
    for h in range(self.polelength):
     if px<x:xh=h
     elif px>x:xh=-h
     elif py<y:yh=h
     elif py>y:yh=-h
     elif pz<z:zh=h
     else:zh=-h
     add_block(self.protocol,self.player_id,x+xh,y+yh,z+zh,self.color)
    self.pole=False
    return False
   if self.posy:
    gx=self.pox*2-x
    gy=self.poy*2-y
    add_block(self.protocol,self.player_id,gx,gy,z,self.color)
   return connection.on_block_build_attempt(self,x,y,z)
  def on_block_destroy(self,x,y,z,value):
   if self.box==2:
    self.send_chat('Second block selected')
    px=self.boxpr[0]
    py=self.boxpr[1]
    pz=self.boxpr[2]
    [ax,bx]=sorted([x,px])
    [ay,by]=sorted([y,py])
    [az,bz]=sorted([z,pz])
    for dx in range(ax,bx+1):
     for dy in range(ay,by+1):
      for dz in range(az,bz+1):
       if dx==ax or dy==ay or dz==az or dx==bx or dy==by or dz==bz:
        add_block(self.protocol,self.player_id,dx,dy,dz,self.color)
    self.box=0
    return False
   elif self.box==1:
    self.boxpr=[x,y,z]
    self.box=2
    self.send_chat("First block selected")
    return False
   return connection.on_block_destroy(self,x,y,z,value)
  def on_animation_update(self,jump,crouch,sneak,sprint):
   if self.tool==SPADE_TOOL and self.dash and sneak:
    pos=self.world_object.position
    ori=self.world_object.orientation.get()
    dashmove(self,pos,ori)
   return connection.on_animation_update(self,jump,crouch,sneak,sprint)
 return protocol,BTconnection